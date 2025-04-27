import logging
import hashlib
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.services.chroma_client import get_vector_db_client
from app.services.embedding_service import get_embedding_model
from app.utils.rag_utils import load_components, create_bm25_index, create_retrievers, create_rag_pipeline, index_vector_data
from app.utils.similarity import compute_similarity_score
from app.utils.llm_augmentation import llm_summarize
from app.models.models import ConfluencePage
from app.utils.dspy_utils import get_openrouter_llm

from app.core.config import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "confluence_pages"

# --- LOGGING INSTRUMENTATION START ---
def log_ingest_start(url, extra_metadata):
    logger.info(f"[INGEST][START] Confluence ingest called. URL: {url}, Extra metadata keys: {list(extra_metadata.keys()) if extra_metadata else None}")

def log_ingest_success(ids):
    logger.info(f"[INGEST][SUCCESS] Confluence page(s) successfully ingested. IDs: {ids}")

def log_ingest_failure(error):
    logger.error(f"[INGEST][FAILURE] Confluence ingest failed: {error}")

def log_search_start(query_text, limit):
    logger.info(f"[SEARCH][START] Confluence search called. Query: '{query_text}', Limit: {limit}")

def log_search_success(results_count):
    logger.info(f"[SEARCH][SUCCESS] Confluence search returned {results_count} results.")

def log_search_failure(error):
    logger.error(f"[SEARCH][FAILURE] Confluence search failed: {error}")
# --- LOGGING INSTRUMENTATION END ---

# Cache pipeline at module level to avoid reloading every call
_rag_pipeline = None
_corpus = None

def _get_rag_pipeline():
    global _rag_pipeline, _corpus
    if _rag_pipeline is not None:
        return _rag_pipeline
    from app.core.config import settings
    client = get_vector_db_client()
    collection = client.get_or_create_collection(COLLECTION_NAME)
    all_docs = collection.get()["documents"]
    _corpus = all_docs
    # Determine db_type and db_path
    db_type = getattr(collection, '_client', None)
    if db_type and 'faiss' in str(type(collection._client)).lower():
        db_type = 'faiss'
        db_path = getattr(collection._client, 'base_path', None)
    else:
        db_type = 'chroma'
        db_path = getattr(collection._client, '_settings', {}).get('path', None)
    embedder, reranker, _, _ = load_components(
        db_type=db_type,
        db_path=db_path,
        embedder_model=None,
        reranker_model=None,
        llm=None
    )
    # Use OpenRouter LLM via DSPy
    llm = get_openrouter_llm()
    bm25_processor = create_bm25_index(_corpus)
    vector_retriever, bm25_retriever = create_retrievers(collection, embedder, bm25_processor, _corpus)
    _rag_pipeline = create_rag_pipeline(vector_retriever, bm25_retriever, reranker, llm)
    return _rag_pipeline

def fetch_confluence_content(confluence_url: str) -> Optional[dict]:
    """
    Fetch the main content from a Confluence page.
    Returns a dict with plain text content, display_title, and raw HTML body for richer search results.
    Uses Basic Auth with username and password for Confluence Server authentication.
    """
    try:
        import os
        from requests.auth import HTTPBasicAuth
        username = os.environ.get("CONFLUENCE_USERNAME")
        password = os.environ.get("CONFLUENCE_PASSWORD")
        if not username or not password:
            raise ValueError("Confluence username or password not set in environment variables CONFLUENCE_USERNAME and CONFLUENCE_PASSWORD.")
        response = requests.get(confluence_url, auth=HTTPBasicAuth(username, password))
        print(f"Confluence fetch status: {response.status_code}")
        print(f"Confluence fetch content (first 500 chars): {response.text[:500]}")
        response.raise_for_status()
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")
        main_content = soup.find("div", {"id": "main-content"})
        if not main_content:
            main_content = soup.body
        text_content = main_content.get_text(separator="\n", strip=True) if main_content else soup.get_text(separator="\n", strip=True)
        title_tag = soup.find("title")
        h1_tag = soup.find("h1")
        display_title = (h1_tag.get_text(strip=True) if h1_tag else (title_tag.get_text(strip=True) if title_tag else None))
        if not display_title and text_content:
            display_title = next((line for line in text_content.splitlines() if line.strip()), None)
        html_body = str(main_content) if main_content else str(soup.body)
        return {
            "content": text_content,
            "display_title": display_title,
            "html_body": html_body
        }
    except Exception as e:
        logger.error(f"Error fetching Confluence content: {str(e)}")
        return None

def add_confluence_page_to_vectordb(
    confluence_url: str,
    extra_metadata: Optional[Dict[str, Any]] = None,
    llm_augment: Optional[Any] = None,
    augment_metadata: bool = False,
    normalize_language: bool = False,
    target_language: str = "en"
) -> Optional[List[str]]:
    log_ingest_start(confluence_url, extra_metadata)
    try:
        page_data = fetch_confluence_content(confluence_url)
        if not page_data or not page_data.get("content"):
            raise ValueError("Failed to fetch content from Confluence URL")
        content = page_data["content"]
        display_title = page_data.get("display_title")
        html_body = page_data.get("html_body")
        client = get_vector_db_client()
        embedder = get_embedding_model()
        content_hash = hashlib.sha256((content or "").encode("utf-8")).hexdigest()
        page_id = f"confluence_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        # Use ConfluencePage model for structured metadata
        page_obj = ConfluencePage(
            page_id=page_id,
            title=display_title or "Confluence Page",
            url=confluence_url,
            space=page_data.get("space"),
            labels=page_data.get("labels"),
            creator=page_data.get("creator"),
            created=page_data.get("created"),
            updated=page_data.get("updated"),
            content=content,
            similarity_score=None,
            metadata=extra_metadata,
        )
        metadata = page_obj.model_dump()
        # Use unified ingest utility with configurable augmentation
        ids = index_vector_data(
            client=client,
            embedder=embedder,
            documents=[content],
            doc_ids=[page_id],
            collection_name="confluence_pages",
            metadatas=[metadata],
            clear_existing=False,
            deduplicate=True,
            llm_augment=llm_augment or llm_summarize,
            augment_metadata=augment_metadata,
            normalize_language=normalize_language,
            target_language=target_language
        )
        log_ingest_success(ids)
        return ids
    except Exception as e:
        log_ingest_failure(e)
        return None

def search_similar_confluence_pages(query_text: str, limit: int = 10):
    log_search_start(query_text, limit)
    try:
        rag_pipeline = _get_rag_pipeline()
        rag_result = rag_pipeline.forward(query_text)
        formatted = []
        for idx, context in enumerate(rag_result.context):
            formatted.append({
                "id": f"rag_{idx}",
                "title": context[:60],
                "content": context,
                "similarity_score": 1.0 if idx == 0 else 0.8,
                "metadata": {},
                "llm_answer": rag_result.answer if idx == 0 else None
            })
        log_search_success(len(formatted))
        return formatted
    except Exception as e:
        log_search_failure(e)
        return []
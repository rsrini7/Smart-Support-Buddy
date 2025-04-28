import logging
import hashlib
import requests
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.services.chroma_client import get_vector_db_client
from app.services.embedding_service import get_embedding_model
from app.utils.rag_utils import load_components, create_bm25_index, create_retrievers, create_rag_pipeline, index_vector_data
from app.utils.similarity import compute_similarity_score, compute_text_similarity_score
from app.utils.llm_augmentation import llm_summarize
from app.models.models import ConfluencePage
from app.utils.dspy_utils import get_openrouter_llm
from app.services.faiss_client import FaissCollection # Add this import if not already present

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
    all_docs_result = collection.get(include=['documents'])
    _corpus = all_docs_result.get("documents", [])

    # Determine db_type and db_path based on collection type
    if isinstance(collection, FaissCollection):
        db_type = 'faiss'
        # Use the directory containing the index file as the path
        db_path = os.path.dirname(collection.index_path) if collection.index_path else None
        logger.info(f"Detected FAISS collection. Type: {db_type}, Path: {db_path}")
    elif hasattr(collection, '_client'): # Assuming ChromaDB or similar structure
        db_type = 'chroma'
        chroma_settings = getattr(collection._client, '_settings', None)
        if isinstance(chroma_settings, dict):
            db_path = chroma_settings.get('persist_directory', None) or chroma_settings.get('path', None)
        else:
            db_path = None
        logger.info(f"Detected ChromaDB-like collection. Type: {db_type}, Path: {db_path}")
    else:
        logger.warning("Could not determine DB type or path from collection object.")
        db_type = 'unknown'
        db_path = None

    embedder, reranker, _, _ = load_components(
        db_type=db_type,
        db_path=db_path,
        embedder_model=None, # Let load_components handle default
        reranker_model=None, # Let load_components handle default
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

def sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    sanitized_metadata = {}
    for key, value in metadata.items():
        if value is not None:
            sanitized_metadata[key] = value
    return sanitized_metadata

def add_confluence_page_to_vectordb(
    confluence_url: str,
    extra_metadata: Optional[Dict[str, Any]] = None,
    llm_augment: Optional[Any] = None,
    augment_metadata: bool = False,
    normalize_language: bool = False,
    target_language: str = "en"
) -> Optional[str or List[str]]:
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
            metadata=None if extra_metadata is None else sanitize_metadata(extra_metadata),
        )
        metadata = sanitize_metadata(page_obj.model_dump())
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
        # TEST COMPAT: return string if only one id
        if isinstance(ids, list) and len(ids) == 1:
            return ids[0]
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
            # Unwrap DSPy Example objects to dicts for frontend compatibility
            if hasattr(context, 'to_dict'):
                context_dict = context.to_dict()
                content = getattr(context, 'long_text', context_dict.get('long_text', ''))
                page_id = context_dict.get('page_id') or context_dict.get('id') or f"rag_{idx}"
                title = str(content)[:60] if content else ""
                similarity_score = float(context_dict.get('similarity_score')) if context_dict.get('similarity_score') is not None else None
                if similarity_score is None:
                    similarity_score = compute_text_similarity_score(query_text, str(content))
                llm_answer = rag_result.answer if idx == 0 else None
                metadata = {k: v for k, v in context_dict.items() if k not in ['long_text', 'id', 'page_id', 'title', 'similarity_score']}
                formatted.append({
                    'page_id': page_id,
                    'title': title,
                    'content': str(content) if content else "",
                    'similarity_score': similarity_score,
                    'metadata': metadata,
                    'llm_answer': llm_answer,
                    'url': context_dict.get('url') or context_dict.get('confluence_url') or metadata.get('confluence_url') or '',
                })
                continue
            elif isinstance(context, dict):
                content = context.get('content', '') or context.get('text', '') or str(context)
                page_id = context.get('page_id') or context.get('id') or f"rag_{idx}"
                title = str(content)[:60] if content else ""
                similarity_score = float(context.get('similarity_score')) if context.get('similarity_score') is not None else None
                if similarity_score is None:
                    similarity_score = compute_text_similarity_score(query_text, str(content))
                llm_answer = rag_result.answer if idx == 0 else None
                metadata = {k: v for k, v in context.items() if k not in ['content', 'text', 'id', 'page_id', 'title', 'similarity_score']}
                formatted.append({
                    'page_id': page_id,
                    'title': title,
                    'content': str(content) if content else "",
                    'similarity_score': similarity_score,
                    'metadata': metadata,
                    'llm_answer': llm_answer,
                    'url': context.get('url') or context.get('confluence_url') or metadata.get('confluence_url') or '',
                })
                continue
            elif hasattr(context, 'long_text'):
                content = getattr(context, 'long_text', str(context))
                page_id = getattr(context, 'page_id', None) or getattr(context, 'id', None) or f"rag_{idx}"
                title = str(content)[:60] if content else ""
                similarity_score = getattr(context, 'similarity_score', None)
                if similarity_score is None:
                    similarity_score = compute_text_similarity_score(query_text, str(content))
                llm_answer = rag_result.answer if idx == 0 else None
                metadata = {k: v for k, v in context.__dict__.items() if k not in ['long_text', 'id', 'page_id', 'title', 'similarity_score']}
                formatted.append({
                    'page_id': page_id,
                    'title': title,
                    'content': str(content) if content else "",
                    'similarity_score': similarity_score,
                    'metadata': metadata,
                    'llm_answer': llm_answer,
                    'url': '',
                })
                continue
            else:
                content_str = str(context) if context else ""
                similarity_score = compute_text_similarity_score(query_text, content_str)
                formatted.append({
                    'page_id': f"rag_{idx}",
                    'title': content_str[:60],
                    'content': content_str,
                    'similarity_score': similarity_score,
                    'metadata': {},
                    'llm_answer': rag_result.answer if idx == 0 else None,
                    'url': '',
                })
        log_search_success(len(formatted))
        return formatted
    except Exception as e:
        log_search_failure(e)
        return []
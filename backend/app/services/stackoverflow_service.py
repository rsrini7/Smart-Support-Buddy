import logging
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.services.chroma_client import get_vector_db_client
from app.services.embedding_service import get_embedding_model
from app.services.rerank_service import get_reranker
import re
import requests
from app.utils.similarity import compute_similarity_score
from app.utils.rag_utils import load_components, create_bm25_index, create_retrievers, create_rag_pipeline, index_vector_data
from app.utils.llm_augmentation import llm_summarize
from app.models.models import StackOverflowQA
from app.utils.dspy_utils import get_openrouter_llm
import dspy

logger = logging.getLogger(__name__)

COLLECTION_NAME = "stackoverflow_qa"

# --- LOGGING INSTRUMENTATION START ---
def log_ingest_start(url, extra_metadata):
    logger.info(f"[INGEST][START] Stack Overflow ingest called. URL: {url}, Extra metadata keys: {list(extra_metadata.keys()) if extra_metadata else None}")

def log_ingest_success(ids):
    logger.info(f"[INGEST][SUCCESS] Stack Overflow Q&A successfully ingested. IDs: {ids}")

def log_ingest_failure(error):
    logger.error(f"[INGEST][FAILURE] Stack Overflow ingest failed: {error}")

def log_search_start(query_text, limit):
    logger.info(f"[SEARCH][START] Stack Overflow search called. Query: '{query_text}', Limit: {limit}")

def log_search_success(results_count):
    logger.info(f"[SEARCH][SUCCESS] Stack Overflow search returned {results_count} results.")

def log_search_failure(error):
    logger.error(f"[SEARCH][FAILURE] Stack Overflow search failed: {error}")
# --- LOGGING INSTRUMENTATION END ---

# Cache pipeline at module level to avoid reloading every call
_rag_pipeline = None
_corpus = None

def _get_rag_pipeline():
    global _rag_pipeline, _corpus
    if _rag_pipeline is not None:
        return _rag_pipeline
    client = get_vector_db_client()
    collection = client.get_collection(COLLECTION_NAME)
    results = collection.get()
    documents = results.get("documents", [])
    _corpus = documents
    embedder = get_embedding_model()
    reranker = get_reranker()  # FIX: use actual reranker model
    # Use OpenRouter LLM via DSPy
    llm = get_openrouter_llm()
    bm25_processor = create_bm25_index(_corpus)
    vector_retriever, bm25_retriever = create_retrievers(collection, embedder, bm25_processor, _corpus)
    _rag_pipeline = create_rag_pipeline(vector_retriever, bm25_retriever, reranker, llm)
    return _rag_pipeline

def extract_question_id(stackoverflow_url: str) -> Optional[str]:
    """
    Extract the question ID from a Stack Overflow URL.
    Example: https://stackoverflow.com/questions/12345678/title-text
    """
    try:
        match = re.search(r'/questions/(\d+)', stackoverflow_url)
        if match:
            return match.group(1)
        else:
            logger.error(f"Could not extract question ID from URL: {stackoverflow_url}")
            return None
    except Exception as e:
        logger.error(f"Error extracting question ID: {str(e)}")
        return None

def fetch_stackoverflow_content(stackoverflow_url: str) -> Optional[Dict[str, Any]]:
    """
    Fetch question and answers from Stack Exchange API for a given Stack Overflow URL.
    Returns a dict with question and answers as plain text.
    """
    try:
        question_id = extract_question_id(stackoverflow_url)
        if not question_id:
            raise ValueError("Invalid Stack Overflow URL or could not extract question ID.")

        # Fetch question
        api_url = f"https://api.stackexchange.com/2.3/questions/{question_id}?order=desc&sort=activity&site=stackoverflow&filter=withbody"
        resp = requests.get(api_url)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("items"):
            raise ValueError("No question found for the given ID.")

        question = data["items"][0]
        question_text = question.get("title", "") + "\n" + question.get("body", "")
        question_text = strip_html_tags(question_text)

        # Fetch answers
        answers_api_url = f"https://api.stackexchange.com/2.3/questions/{question_id}/answers?order=desc&sort=activity&site=stackoverflow&filter=withbody"
        answers_resp = requests.get(answers_api_url)
        answers_resp.raise_for_status()
        answers_data = answers_resp.json()
        answers = []
        for ans in answers_data.get("items", []):
            ans_text = ans.get("body", "")
            ans_text = strip_html_tags(ans_text)
            answers.append({
                "answer_id": ans.get("answer_id"),
                "question_id": question_id,  # Ensure question_id is present in every answer
                "text": ans_text,
                "is_accepted": ans.get("is_accepted", False),
                "score": ans.get("score", 0)
            })

        return {
            "question_id": question_id,
            "question_title": question.get("title", ""),
            "question_text": question_text,
            "question_url": stackoverflow_url,
            "answers": answers
        }
    except Exception as e:
        logger.error(f"Error fetching Stack Overflow content: {str(e)}")
        return None

def strip_html_tags(html: str) -> str:
    """
    Remove HTML tags from a string.
    """
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(separator="\n", strip=True)
    except Exception as e:
        logger.error(f"Error stripping HTML tags: {str(e)}")
        return html

def add_stackoverflow_qa_to_vectordb(
    stackoverflow_url: str,
    extra_metadata: Optional[Dict[str, Any]] = None,
    llm_augment: Optional[Any] = None,
    augment_metadata: bool = False,
    normalize_language: bool = False,
    target_language: str = "en"
) -> Optional[List[str]]:
    log_ingest_start(stackoverflow_url, extra_metadata)
    try:
        content = fetch_stackoverflow_content(stackoverflow_url)
        if not content:
            raise ValueError("Failed to fetch content from Stack Overflow URL")
        client = get_vector_db_client()
        embedder = get_embedding_model()
        ids, documents, metadatas = [], [], []
        # Add question
        question_id = content["question_id"]
        qid = f"soq_{question_id}"
        question_obj = StackOverflowQA(
            question_id=str(question_id),
            question_text=content["question_text"],
            answer_id=None,
            answer_text=None,
            tags=content.get("tags"),
            author=content.get("author"),
            creation_date=content.get("creation_date"),
            score=content.get("score"),
            link=content.get("link"),
            content_hash=None,
            similarity_score=None,
            metadata=None if extra_metadata is None else sanitize_metadata(extra_metadata),
        )
        ids.append(qid)
        documents.append(content["question_text"])
        metadatas.append(sanitize_metadata(question_obj.model_dump()))
        # Add answers
        for ans in content.get("answers", []):
            aid = f"soa_{ans['answer_id']}"
            answer_obj = StackOverflowQA(
                question_id=str(ans["question_id"]),
                question_text=ans["text"],
                answer_id=str(ans.get("answer_id")) if ans.get("answer_id") is not None else None,
                answer_text=ans.get("text"),
                tags=None,
                author=ans.get("author"),
                creation_date=ans.get("creation_date"),
                score=ans.get("score"),
                link=None,
                content_hash=None,
                similarity_score=None,
                metadata=None,
            )
            ids.append(aid)
            documents.append(ans["text"])
            metadatas.append(sanitize_metadata(answer_obj.model_dump()))
        # Use unified ingest utility with configurable augmentation
        index_vector_data(
            client=client,
            embedder=embedder,
            documents=documents,
            doc_ids=ids,
            collection_name=COLLECTION_NAME,
            metadatas=metadatas,
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

def sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    sanitized = {}
    for k, v in metadata.items():
        if v is None:
            sanitized[k] = ""
        elif isinstance(v, list):
            sanitized[k] = ", ".join(str(item) for item in v)
        else:
            sanitized[k] = v
    return sanitized

def search_similar_stackoverflow_content(query_text: str, limit: int = 10):
    log_search_start(query_text, limit)
    try:
        rag_pipeline = _get_rag_pipeline()
        rag_result = rag_pipeline.forward(query_text)
        # Return as a list of dicts for frontend compatibility
        formatted = []
        for idx, context in enumerate(rag_result.context):
            # Unwrap DSPy Example objects to dicts for frontend compatibility
            if hasattr(context, 'to_dict'):
                context_dict = context.to_dict()
                content = getattr(context, 'long_text', context_dict.get('long_text', ''))
                item_id = context_dict.get('item_id') or context_dict.get('id') or f"rag_{idx}"
                title = str(content)[:60] if content else ""
                similarity_score = float(context_dict.get('similarity_score') or (1.0 if idx == 0 else 0.8))
                llm_answer = rag_result.answer if idx == 0 else None
                metadata = {k: v for k, v in context_dict.items() if k not in ['long_text', 'id', 'item_id', 'title', 'similarity_score']}
                question_id = context_dict.get('question_id') or metadata.get('question_id')
                url = (
                    context_dict.get('url')
                    or context_dict.get('link')
                    or metadata.get('url')
                    or (f"https://stackoverflow.com/questions/{question_id}" if question_id else "")
                )
                formatted.append({
                    'item_id': item_id,
                    'title': title,
                    'content': str(content) if content else "",
                    'similarity_score': similarity_score,
                    'metadata': metadata,
                    'llm_answer': llm_answer,
                    'url': url,
                })
                continue
            elif isinstance(context, dict):
                content = context.get('content', '') or context.get('text', '') or str(context)
                item_id = context.get('item_id') or context.get('id') or f"rag_{idx}"
                title = str(content)[:60] if content else ""
                similarity_score = float(context.get('similarity_score') or (1.0 if idx == 0 else 0.8))
                llm_answer = rag_result.answer if idx == 0 else None
                metadata = {k: v for k, v in context.items() if k not in ['content', 'text', 'id', 'item_id', 'title', 'similarity_score']}
                question_id = context.get('question_id') or metadata.get('question_id')
                url = (
                    context.get('url')
                    or context.get('link')
                    or metadata.get('url')
                    or (f"https://stackoverflow.com/questions/{question_id}" if question_id else "")
                )
                formatted.append({
                    'item_id': item_id,
                    'title': title,
                    'content': str(content) if content else "",
                    'similarity_score': similarity_score,
                    'metadata': metadata,
                    'llm_answer': llm_answer,
                    'url': url,
                })
                continue
            elif hasattr(context, 'long_text'):
                content = getattr(context, 'long_text', str(context))
                item_id = getattr(context, 'item_id', None) or getattr(context, 'id', None) or f"rag_{idx}"
                title = str(content)[:60] if content else ""
                similarity_score = float(getattr(context, 'similarity_score', 1.0 if idx == 0 else 0.8) or (1.0 if idx == 0 else 0.8))
                llm_answer = rag_result.answer if idx == 0 else None
                metadata = {k: v for k, v in context.__dict__.items() if k not in ['long_text', 'id', 'item_id', 'title', 'similarity_score']}
                question_id = getattr(context, 'question_id', None) or metadata.get('question_id')
                url = (
                    getattr(context, 'url', None)
                    or getattr(context, 'link', None)
                    or metadata.get('url')
                    or (f"https://stackoverflow.com/questions/{question_id}" if question_id else "")
                )
                formatted.append({
                    'item_id': item_id,
                    'title': title,
                    'content': str(content) if content else "",
                    'similarity_score': similarity_score,
                    'metadata': metadata,
                    'llm_answer': llm_answer,
                    'url': url,
                })
                continue
            else:
                content_str = str(context) if context else ""
                formatted.append({
                    'item_id': f"rag_{idx}",
                    'title': content_str[:60],
                    'content': content_str,
                    'similarity_score': float(1.0 if idx == 0 else 0.8),
                    'metadata': {},
                    'llm_answer': rag_result.answer if idx == 0 else None,
                    'url': '',
                })
        log_search_success(len(formatted))
        return formatted
    except Exception as e:
        log_search_failure(e)
        return []
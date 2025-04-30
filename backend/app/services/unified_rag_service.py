import logging
from typing import List, Dict, Any, Optional
from app.services.chroma_client import get_vector_db_client
from app.services.embedding_service import get_embedding_model
from app.utils.rag_utils import create_bm25_index, create_retrievers, create_rag_pipeline
from app.utils.llm_augmentation import llm_summarize
from app.utils.dspy_utils import get_openrouter_llm

logger = logging.getLogger(__name__)

# --- Unified RAG Search across Issues, Jira, MSG ---
COLLECTIONS = [
    ("issues", "issue_id"),
    ("jira_tickets", "jira_ticket_id"),
    ("msg_files", "msg_file_path"),
]

def get_unified_corpus():
    """
    Loads all documents and metadata from all RAG-enabled collections.
    Returns: (documents, metadatas, ids, collection_names)
    """
    client = get_vector_db_client()
    all_docs, all_metas, all_ids, all_collections = [], [], [], []
    for cname, id_key in COLLECTIONS:
        collection = client.get_collection(cname)
        results = collection.get()
        docs = results.get("documents", [])
        metas = results.get("metadatas", [])
        ids = results.get("ids", [])
        all_docs.extend(docs)
        all_metas.extend(metas)
        all_ids.extend(ids)
        all_collections.extend([cname]*len(docs))
    return all_docs, all_metas, all_ids, all_collections

_rag_pipeline = None
_corpus = None


def _get_rag_pipeline(use_llm: bool = False):
    global _rag_pipeline, _corpus
    if _rag_pipeline is not None:
        return _rag_pipeline
    from app.core.config import settings
    import dspy
    docs, metas, ids, colnames = get_unified_corpus()
    _corpus = docs
    embedder = get_embedding_model()
    client = get_vector_db_client()
    # Use OpenRouter LLM via DSPy
    llm = None
    if use_llm:
        llm = get_openrouter_llm()
    bm25_processor = create_bm25_index(_corpus)
    # SyntheticCollection logic omitted for brevity, keep as is if needed
    vector_retriever, bm25_retriever = create_retrievers(client, embedder, bm25_processor, _corpus)
    _rag_pipeline = create_rag_pipeline(vector_retriever, bm25_retriever, None, llm)
    return _rag_pipeline


def unified_rag_search(query_text: str, limit: int = 10, use_llm: bool = False) -> List[Dict[str, Any]]:
    """
    Hybrid RAG search across Issues, Jira, and MSG files.
    Returns fused, reranked, and LLM-augmented results from all sources.
    """
    logger.info(f"[UNIFIED_RAG][START] Unified search called. Query: '{query_text}', Limit: {limit}")
    try:
        _get_rag_pipeline(use_llm=use_llm)
        rag_result = _rag_pipeline.forward(query_text)
        formatted = []
        for idx, context in enumerate(rag_result.context):
            formatted.append({
                "id": f"unified_rag_{idx}",
                "title": context[:150]+" ...",
                "content": context,
                "similarity_score": 1.0 if idx == 0 else 0.8,
                "metadata": {},
                "llm_answer": rag_result.answer if idx == 0 else None
            })
        logger.info(f"[UNIFIED_RAG][SUCCESS] Unified search returned {len(formatted)} results.")
        return formatted
    except Exception as e:
        logger.error(f"[UNIFIED_RAG][FAILURE] Unified search failed: {e}")
        return []

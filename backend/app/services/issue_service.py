from typing import Optional, List, Dict, Any
from app.services.chroma_client import get_collection
from app.services.embedding_service import get_embedding_model
from app.services.faiss_client import FaissCollection
from app.utils.rag_utils import index_vector_data
from app.utils.llm_augmentation import llm_summarize
from app.models import IssueResponse
from datetime import datetime
import logging
import re
from app.utils.similarity import compute_similarity_score
# --- DSPy RAG imports ---
from app.utils.rag_utils import load_components, create_bm25_index, create_retrievers, create_rag_pipeline
from app.utils.dspy_utils import get_openrouter_llm

logger = logging.getLogger(__name__)

COLLECTION_NAME = "issues"

# Cache pipeline at module level to avoid reloading every call
_rag_pipeline = None
_corpus = None

def _get_rag_pipeline():
    global _rag_pipeline, _corpus
    if _rag_pipeline is not None:
        return _rag_pipeline
    from app.core.config import settings
    import dspy
    collection = get_collection(COLLECTION_NAME)
    all_docs = collection.get()["documents"]
    _corpus = all_docs
    # Determine db_type and db_path robustly
    if isinstance(collection, FaissCollection):
        db_type = 'faiss'
        db_path = getattr(collection, 'index_path', None)
    else:
        db_type = 'chroma'
        db_path = getattr(collection, '_client', None)
        if db_path:
            db_path = getattr(collection._client, '_settings', {}).get('path', None)
    embedder, reranker, client, _ = load_components(
        db_type=db_type,
        db_path=db_path,
        embedder_model=None,  # Use default or settings
        reranker_model=None,  # Use default or settings
        llm=None
    )
    # Use OpenRouter LLM via DSPy
    llm = get_openrouter_llm()
    bm25_processor = create_bm25_index(_corpus)
    vector_retriever, bm25_retriever = create_retrievers(collection, embedder, bm25_processor, _corpus)
    _rag_pipeline = create_rag_pipeline(vector_retriever, bm25_retriever, reranker, llm)
    return _rag_pipeline

def delete_issue(issue_id: str) -> bool:
    try:
        collection = get_collection(COLLECTION_NAME)
        collection.delete(ids=[issue_id])
        return True
    except Exception as e:
        logger.error(f"Error deleting issue from vector database: {str(e)}")
        return False

def get_issue(issue_id: str) -> Optional[IssueResponse]:
    try:
        collection = get_collection(COLLECTION_NAME)
        result = collection.get(ids=[issue_id])
        if not result or not result['ids']:
            return None
        metadata = result['metadatas'][0]
        document = result['documents'][0]
        # Fetch Jira data if needed (optional)
        jira_data = None
        try:
            from app.services.jira_service import get_jira_ticket
            if isinstance(metadata, list):
                metadata = {}
            # FIX: Try both jira_ticket_id and msg_jira_id
            jira_ticket_id = metadata.get('jira_ticket_id') or metadata.get('msg_jira_id')
            if jira_ticket_id:
                jira_data = get_jira_ticket(jira_ticket_id)
        except Exception as e:
            logger.warning(f"Failed to fetch Jira data for ticket {metadata.get('jira_ticket_id') or metadata.get('msg_jira_id')}: {e}")
            jira_data = None
        return IssueResponse(
            id=issue_id,
            title=metadata.get('msg_subject', ''),
            description=document,
            jira_ticket_id=metadata.get('jira_ticket_id', '') or metadata.get('msg_jira_id', ''),
            received_date=metadata.get('msg_received_date', '') or metadata.get('created_date', ''),
            created_at=metadata.get('created_at') or metadata.get('created_date') or metadata.get('msg_received_date') or datetime.now(),
            updated_at=None,
            msg_data={
                'subject': metadata.get('msg_subject', ''),
                'body': metadata.get('msg_body', ''),
                'sender': metadata.get('msg_sender', ''),
                'received_date': metadata.get('msg_received_date', ''),
                'jira_id': metadata.get('msg_jira_id', ''),
                'jira_url': metadata.get('msg_jira_url', ''),
                'recipients': metadata.get('recipients', [])
            },
            jira_data=jira_data
        )
    except Exception as e:
        logger.error(f"Error getting issue from vector database: {str(e)}")
        raise

def search_similar_issues(query_text: str = "", jira_ticket_id: Optional[str] = None, limit: int = 10) -> List[IssueResponse]:
    """
    Use the DSPy RAG pipeline for hybrid retrieval and answer generation.
    """
    try:
        rag_pipeline = _get_rag_pipeline()
        # If searching by Jira ticket only, fallback to direct lookup
        if jira_ticket_id and not query_text:
            collection = get_collection(COLLECTION_NAME)
            results = collection.get(
                where={"$and": [
                    {"$or": [
                        {"jira_ticket_id": jira_ticket_id.upper()},
                        {"jira_ticket_id": jira_ticket_id.lower()},
                        {"msg_jira_id": jira_ticket_id.upper()},
                        {"msg_jira_id": jira_ticket_id.lower()}
                    ]}
                ]},
                limit=limit,
            )
            # Format as IssueResponse
            issue_responses = []
            for idx, issue_id in enumerate(results.get("ids", [])):
                metadata = results["metadatas"][idx]
                document = results["documents"][idx]
                issue_responses.append(IssueResponse(
                    id=issue_id,
                    title=metadata.get('msg_subject', ''),
                    description=document,
                    jira_ticket_id=metadata.get('jira_ticket_id', '') or metadata.get('msg_jira_id', ''),
                    received_date=metadata.get('msg_received_date', '') or metadata.get('created_date', ''),
                    created_at=metadata.get('created_at') or metadata.get('created_date') or metadata.get('msg_received_date') or datetime.now(),
                    updated_at=None,
                    msg_data={
                        'subject': metadata.get('msg_subject', ''),
                        'body': metadata.get('msg_body', ''),
                        'sender': metadata.get('msg_sender', ''),
                        'received_date': metadata.get('msg_received_date', ''),
                        'jira_id': metadata.get('msg_jira_id', ''),
                        'jira_url': metadata.get('msg_jira_url', ''),
                        'recipients': metadata.get('recipients', [])
                    },
                    jira_data=None
                ))
            return issue_responses
        # Otherwise, use the RAG pipeline
        rag_result = rag_pipeline.forward(query_text)
        # Return as IssueResponse list (one for each context doc)
        responses = []
        for idx, context in enumerate(rag_result.context):
            responses.append(IssueResponse(
                id=f"rag_{idx}",
                title=context[:60],
                description=context,
                jira_ticket_id="",
                received_date="",
                created_at=datetime.now(),
                updated_at=None,
                msg_data={},
                jira_data=None,
                llm_answer=rag_result.answer if idx == 0 else None
            ))
        return responses
    except Exception as e:
        logger.error(f"Error in DSPy RAG search_similar_issues: {str(e)}")
        return []

def add_issue_to_vectordb(
    issue: Dict[str, Any],
    extra_metadata: Optional[Dict[str, Any]] = None,
    llm_augment: Optional[Any] = None,
    augment_metadata: bool = True,
    normalize_language: bool = True,
    target_language: str = "en"
) -> Optional[str]:
    """
    Add an issue to the vector database with optional LLM-based augmentation and deduplication.
    """
    try:
        client = get_collection(COLLECTION_NAME)._client
        embedder = get_embedding_model()
        issue_id = issue.get("id") or f"issue_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        title = issue.get("title", "")
        description = issue.get("description", "")
        document = f"{title}\n{description}".strip()
        import hashlib
        content_hash = hashlib.sha256(document.encode('utf-8')).hexdigest()
        metadata = {
            "msg_subject": title,
            "msg_body": description,
            "created_date": issue.get("created_at", str(datetime.now())),
            "jira_ticket_id": issue.get("jira_ticket_id"),
            "content_hash": content_hash,
        }
        if extra_metadata:
            metadata.update(extra_metadata)
        index_vector_data(
            client=client,
            embedder=embedder,
            documents=[document],
            doc_ids=[issue_id],
            collection_name=COLLECTION_NAME,
            metadatas=[metadata],
            clear_existing=False,
            deduplicate=True,
            llm_augment=llm_augment or llm_summarize,
            augment_metadata=augment_metadata,
            normalize_language=normalize_language,
            target_language=target_language
        )
        return issue_id
    except Exception as e:
        logger.error(f"Error adding issue to vector database: {str(e)}")
        return None

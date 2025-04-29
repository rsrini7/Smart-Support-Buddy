from typing import Optional, List, Dict, Any
from app.services.chroma_client import get_collection
from app.services.embedding_service import get_embedding_model
from app.services.faiss_client import FaissCollection
from app.utils.rag_utils import index_vector_data
from app.utils.llm_augmentation import llm_summarize
from app.models import IssueResponse
from datetime import datetime
import logging
import os
from app.utils.similarity import compute_text_similarity_score
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
    # Fetch documents, IDs, and metadata together
    all_data = collection.get(include=['documents', 'metadatas'])
    _corpus = all_data.get("documents", [])
    _ids = all_data.get("ids", [])
    _metadatas = all_data.get("metadatas", [])
    # Store mapping for BM25 retriever if needed, or pass necessary info
    # For now, just ensure _corpus is the list of documents for BM25 index
    # The create_retrievers function will need adjustment to pass IDs/Metas to BM25Retriever
    # Determine db_type and db_path robustly
    if isinstance(collection, FaissCollection):
        db_type = 'faiss'
        # Use the directory containing the index file
        index_file_path = getattr(collection, 'index_path', None)
        db_path = os.path.dirname(index_file_path) if index_file_path else None
    else:
        db_type = 'chroma'
        chroma_settings = getattr(collection._client, '_settings', None)
        if isinstance(chroma_settings, dict):
            db_path = chroma_settings.get('persist_directory', None) or chroma_settings.get('path', None)
        else:
            db_path = None
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
    # Pass IDs and Metadatas to create_retrievers so BM25Retriever can use them
    vector_retriever, bm25_retriever = create_retrievers(collection, embedder, bm25_processor, _corpus, doc_ids=_ids, metadatas=_metadatas)
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

def search_similar_issues(query_text: str = "", jira_ticket_id: Optional[str] = None, limit: int = 10, use_llm: bool = False) -> List[IssueResponse]:
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
        rag_result = rag_pipeline.forward(query_text, use_llm=use_llm)
        # Process RAG results, using retrieved IDs and metadata
        responses = []
        # The context from RAG is now a list of dspy.Example objects with metadata
        retrieved_examples = rag_result.context
        logger.debug(f"RAG pipeline returned {len(retrieved_examples)} examples.")

        # Fetch full issue details using the IDs from metadata
        issue_ids = [ex.get('id') for ex in retrieved_examples if ex.get('id')]
        logger.debug(f"Extracted issue IDs from RAG context: {issue_ids}") # Added debug log

        # Batch fetch issues if possible, otherwise fetch one by one
        # (Assuming get_issue fetches one by one for simplicity here)
        issues_map = {}
        for issue_id in issue_ids:
            if not issue_id: # Skip if ID is None or empty
                logger.warning("Skipping fetch for None/empty issue ID.")
                continue
            try:
                issue = get_issue(issue_id)
                if issue:
                    issues_map[issue_id] = issue
                    logger.debug(f"Successfully fetched issue {issue_id} for map.") # Added debug log
                else:
                    logger.warning(f"get_issue returned None for issue ID: {issue_id}") # Modified warning log
            except Exception as fetch_err:
                 logger.error(f"Error fetching issue {issue_id} using get_issue: {fetch_err}") # Added error log for fetch exception

        logger.debug(f"Populated issues_map with {len(issues_map)} entries.")

        for idx, example in enumerate(retrieved_examples):
            # Ensure example is treated as a dictionary-like object for .get()
            logger.debug(f"Processing RAG example {idx}: {example}") # Added debug log
            if not hasattr(example, 'get'):
                logger.warning(f"Skipping RAG example {idx} as it's not dictionary-like: {type(example)}")
                continue

            issue_id = example.get('id')
            logger.debug(f"Extracted issue_id from example {idx}: {issue_id}") # Added debug log

            # Check if the issue was successfully fetched and exists in the map
            if issue_id and issue_id in issues_map:
                issue = issues_map[issue_id]
                logger.debug(f"Found issue {issue_id} in issues_map: {issue.model_dump_json(indent=2)}") # Added detailed log
                # Add similarity score if available from RAG metadata
                similarity_score = example.get('score') or compute_text_similarity_score(query_text, issue.description)
                issue.similarity_score = similarity_score
                # Add LLM answer if it's the top result and available
                if idx == 0 and rag_result.answer:
                    issue.llm_answer = rag_result.answer
                responses.append(issue)
            else:
                logger.warning(f"Issue ID {issue_id} from RAG example {idx} not found in issues_map or was None.") # Added warning log

        # Sort by similarity score if available
        responses.sort(key=lambda x: x.similarity_score if x.similarity_score is not None else -1, reverse=True)

        logger.info(f"Search completed. Found {len(responses)} similar issues.")
        return responses[:limit]

    except Exception as e:
        logger.error(f"Error searching similar issues: {str(e)}", exc_info=True)
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

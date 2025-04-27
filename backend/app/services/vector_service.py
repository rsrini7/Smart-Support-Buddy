from typing import List, Optional, Dict, Any
import logging
from app.models import IssueResponse
from app.services.chroma_client import get_vector_db_client
from app.services.vector_issue_service import add_issue_to_vectordb as original_add_issue_to_vectordb
from app.services.issue_service import delete_issue as real_delete_issue, get_issue as real_get_issue
from app.services.chroma_client import clear_collection as real_clear_collection
from app.services.issue_service import search_similar_issues as real_search_similar_issues

logger = logging.getLogger(__name__)

# Existing functions for collection listing and management remain here for now

def get_all_chroma_collections_data() -> list:
    """
    Get all ChromaDB collections and their documents.
    Returns:
        List of dicts, each with collection name and documents.
    """
    try:
        client = get_vector_db_client()
        collections = client.list_collections()
        logger.info(f"ChromaDB list_collections() returned: {collections}")
        all_data = []
        for col in collections:
            # Ensure col is a string (collection name), not a Collection object
            col_name = col.name if hasattr(col, 'name') else col
            collection = client.get_collection(col_name)
            docs = collection.get()
            if docs is None:
                logger.error(f"ChromaDB collection.get() returned None for collection: {col_name}")
                all_data.append({
                    "collection_name": col_name,
                    "records": []
                })
                continue
            ids = docs.get("ids") or []
            embeddings = docs.get("embeddings") or [None] * len(ids)
            documents = docs.get("documents") or [None] * len(ids)
            metadatas = docs.get("metadatas") or [None] * len(ids)
            num_records = len(ids)
            records = []
            for i in range(num_records):
                record = {
                    "id": ids[i],
                    "embedding": embeddings[i] if i < len(embeddings) else None,
                    "document": documents[i] if i < len(documents) else None,
                    "metadata": metadatas[i] if i < len(metadatas) else None,
                }
                records.append(record)
            all_data.append({
                "collection_name": col_name,
                "records": records
            })
        return all_data
    except Exception as e:
        logging.error(f"Error fetching ChromaDB collections data: {str(e)}")
        return []

def add_issue_to_vectordb(msg_data: Optional[Dict[str, Any]] = None, jira_data: Optional[Dict[str, Any]] = None,
                        augment_metadata: bool = True, normalize_language: bool = True, target_language: str = "en") -> str:
    # Defensive patch: if msg_data is an error dict, raise ValueError immediately
    if isinstance(msg_data, dict) and msg_data.get("status") == "error":
        raise ValueError(f"MSG parse error: {msg_data.get('error')}")
    # Compose the issue dict for the underlying implementation
    issue = {}
    if msg_data is not None:
        issue["msg_data"] = msg_data
    if jira_data is not None:
        issue["jira_data"] = jira_data
    # Call the unified add_issue_to_vectordb in vector_issue_service with LLM params
    return original_add_issue_to_vectordb(
        issue=issue,
        augment_metadata=augment_metadata,
        normalize_language=normalize_language,
        target_language=target_language
    )

# Defensive patch: avoid infinite recursion by calling the real implementation
def delete_issue(issue_id: str) -> bool:
    """
    Delete a RCA from the vector database.
    
    Args:
        issue_id: ID of the issue to delete
        
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    return real_delete_issue(issue_id)

# Defensive patch: avoid infinite recursion by calling the real implementation
def get_issue(issue_id: str) -> Optional[IssueResponse]:
    """
    Get a specific RCA by ID from the vector database.
    
    Args:
        issue_id: ID of the issue to retrieve
        
    Returns:
        IssueResponse object if found, None otherwise
    """
    return real_get_issue(issue_id)

def search_similar_issues(query_text: str = "", jira_ticket_id: Optional[str] = None, limit: int = 10) -> List[IssueResponse]:
    """
    Search for similar support issues / queries based on a query text or Jira ticket ID.
    
    Args:
        query_text: Text to search for (optional)
        jira_ticket_id: Optional Jira ticket ID to filter results
        limit: Maximum number of results to return
        
    Returns:
        List of IssueResponse objects representing similar issues
    """
    return real_search_similar_issues(query_text, jira_ticket_id, limit)

def clear_all_issues() -> bool:
    return real_clear_collection("issues")

def clear_collection(collection_name: str) -> bool:
    return real_clear_collection(collection_name)

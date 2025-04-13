from typing import List, Dict, Any, Optional
import os
import logging
import json
from datetime import datetime
from sentence_transformers import SentenceTransformer
import numpy as np
import chromadb
from chromadb.utils import embedding_functions

from app.core.config import settings
from app.db.models import IssueResponse

logger = logging.getLogger(__name__)

# Initialize the vector database client
def get_vector_db_client():
    """
    Get a ChromaDB client instance.
    
    Returns:
        ChromaDB client instance
    """
    try:
        # Disable telemetry before creating the client
        chromadb.configure(anonymized_telemetry=False)
        # Using the new client construction method as per migration guide
        client = chromadb.PersistentClient(path=settings.VECTOR_DB_PATH)
        return client
    except Exception as e:
        logger.error(f"Error initializing vector database client: {str(e)}")
        raise

# Initialize the embedding model
def get_embedding_model():
    """
    Get a sentence transformer model for generating embeddings.
    
    Returns:
        SentenceTransformer model instance
    """
    try:
        model = SentenceTransformer(settings.EMBEDDING_MODEL)
        return model
    except Exception as e:
        logger.error(f"Error initializing embedding model: {str(e)}")
        raise

def add_issue_to_vectordb(msg_data: Optional[Dict[str, Any]] = None, jira_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Add a production issue to the vector database.

    Args:
        msg_data: Optional parsed MSG file data dictionary
        jira_data: Optional Jira ticket data dictionary

    Returns:
        ID of the created issue
    
    Args:
        msg_data: Parsed MSG file data (optional if jira_data is provided)
        jira_data: Optional Jira ticket data
        
    Returns:
        ID of the created issue
    """
    try:
        if msg_data is None:
            msg_data = {}
        if jira_data is None:
            jira_data = {}

         # Ensure at least one of msg_data or jira_data is provided
        if not msg_data and not jira_data:
            raise ValueError("Either MSG data or Jira data must be provided")

        # If jira_data is empty, try to fetch using jira_id from msg_data
        if (not jira_data) and msg_data:
            jira_id_from_msg = msg_data.get("jira_id")
            logger.debug(f"Jira ID from MSG data: {jira_id_from_msg}")
            if jira_id_from_msg:
                try:
                    from app.services.jira_service import get_jira_ticket
                    fetched_jira_data = get_jira_ticket(jira_id_from_msg)
                    if fetched_jira_data:
                        jira_data = fetched_jira_data
                except Exception as e:
                    logger.warning(f"Failed to fetch Jira data for ID {jira_id_from_msg}: {e}")
       
            
        # Get vector DB client
        client = get_vector_db_client()
        
        # Get embedding model
        model = get_embedding_model()

        msg_subject = ""
        msg_body = ""
        
        # Prepare the text to be embedded
        if(msg_data):
            msg_subject = msg_data.get("subject", "")
            msg_body = msg_data.get("body", "")

        # Create a unique ID for the issue
        file_path = msg_data.get('file_path', '') if msg_data else ''
        suffix = os.path.basename(file_path) if file_path else 'no_msgfile'
        issue_id = f"issue_{datetime.now().strftime('%Y%m%d%H%M%S')}_{suffix}"
        
        
        # Combine with Jira data if available
        jira_summary = ""
        jira_description = ""
        jira_ticket_id = None
        
        if jira_data:
            jira_ticket_id = jira_data.get("key")
            jira_summary = jira_data.get("summary", "")
            jira_description = jira_data.get("description", "") or ""
            
        if jira_data:
            comments = jira_data.get("comments", [])
            # Ensure comments is a list
            if isinstance(comments, str):
                comments = [comments]
            elif not isinstance(comments, list):
                comments = []

            if comments:
                formatted_comments = []
                for comment in comments:
                    if isinstance(comment, dict):
                        author_field = comment.get("author", "Unknown Author")
                        if isinstance(author_field, dict):
                            author = author_field.get("displayName", "Unknown Author")
                        else:
                            author = author_field  # assume string
                        body = comment.get("body", "")
                        formatted_comments.append(f"{author}: {body}")
                    else:
                        # comment is likely a plain string
                        formatted_comments.append(str(comment))
                jira_comments_text = "\n".join(formatted_comments)

        # Create the full text for embedding, including comments
        full_text = f"{msg_subject}\n{msg_body}\n{jira_summary}\n{jira_description}"
        if 'jira_comments_text' in locals():
            full_text += f"\nComments:\n{jira_comments_text}"
        
        # Generate embedding
        embedding = model.encode(full_text).tolist()
        
        # Get or create the collection
        collection = client.get_or_create_collection("production_issues")
        
        # Add the document to the collection
        metadata = {
            "msg_subject": msg_subject,
            "msg_body": msg_body,
            "msg_sender": msg_data.get("sender", ""),
            "msg_received_date": msg_data.get("received_date", "").isoformat() if msg_data.get("received_date") else "",
            "msg_jira_id": msg_data.get("jira_id", ""),
            "msg_jira_url": msg_data.get("jira_url", ""),
            "recipients": msg_data.get("recipients", []),
            "attachments": msg_data.get("attachments", []),
            "jira_ticket_id": jira_ticket_id or "",
            "jira_summary": jira_summary,
            # Add current date if no received_date from MSG
            "created_date": datetime.now().isoformat() if not msg_data.get("received_date") else ""
        }

        # Sanitize metadata: replace None with empty strings, convert lists to comma-separated strings
        sanitized_metadata = {}
        for k, v in metadata.items():
            if v is None:
                sanitized_metadata[k] = ""
            elif isinstance(v, list):
                sanitized_metadata[k] = ", ".join(str(item) for item in v)
            else:
                sanitized_metadata[k] = v
        metadata = sanitized_metadata
        
        collection.add(
            ids=[issue_id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[full_text]
        )
        
        # Note: persist() is no longer needed with PersistentClient as it automatically handles persistence
        
        return issue_id
    
    except Exception as e:
        logger.error(f"Error adding issue to vector database: {str(e)}")
        raise

def delete_issue(issue_id: str) -> bool:
    """
    Delete a production issue from the vector database.
    
    Args:
        issue_id: ID of the issue to delete
        
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    try:
        # Get vector DB client
        client = get_vector_db_client()
        
        # Get the collection
        collection = client.get_or_create_collection("production_issues")
        
        # Delete the document from the collection
        collection.delete(ids=[issue_id])
        
        return True
    
    except Exception as e:
        logger.error(f"Error deleting issue from vector database: {str(e)}")
        return False

def get_issue(issue_id: str) -> Optional[IssueResponse]:
    """
    Get a specific production issue by ID from the vector database.
    
    Args:
        issue_id: ID of the issue to retrieve
        
    Returns:
        IssueResponse object if found, None otherwise
    """
    try:
        # Get vector DB client
        client = get_vector_db_client()
        
        # Get the collection
        collection = client.get_or_create_collection("production_issues")
        
        # Get the document by ID
        result = collection.get(ids=[issue_id])
        
        # If no results found, return None
        if not result or not result['ids']:
            return None
            
        # Extract metadata and document
        metadata = result['metadatas'][0]
        document = result['documents'][0]
        
        # Create IssueResponse object
        jira_data = None
        try:
            from app.services.jira_service import get_jira_ticket

            # Defensive fix: if metadata is a list, convert to empty dict
            if isinstance(metadata, list):
                metadata = {}

            if metadata.get('jira_ticket_id'):
                jira_data = get_jira_ticket(metadata.get('jira_ticket_id'))
            else:
                jira_data = None
        except Exception as e:
            logger.warning(f"Failed to fetch Jira data for ticket {metadata.get('jira_ticket_id')}: {e}")
            jira_data = None
        
        return IssueResponse(
            id=issue_id,
            title=metadata.get('msg_subject', ''),
            description=document,
            jira_ticket_id=metadata.get('jira_ticket_id', ''),
            received_date=metadata.get('msg_received_date', '') or metadata.get('created_date', ''),
            created_at=datetime.now(),  # Add required created_at field
            updated_at=None,
            msg_data={
                'subject': metadata.get('msg_subject', ''),
                'body': metadata.get('msg_body', ''),
                'sender': metadata.get('msg_sender', ''),
                'received_date': metadata.get('msg_received_date', ''),
                'jira_id': metadata.get('msg_jira_id', ''),
                'jira_url': metadata.get('msg_jira_url', ''),
                'recipients': metadata.get('recipients', []),
                'attachments': metadata.get('attachments', [])
            },
            jira_data=jira_data
        )
        
    except Exception as e:
        logger.error(f"Error getting issue from vector database: {str(e)}")
        raise

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
    try:
        # Get vector DB client
        client = get_vector_db_client()
        
        # Get the collection
        collection = client.get_or_create_collection("production_issues")
        
        # If only Jira ticket ID is provided, use get() instead of query()
        if jira_ticket_id and not query_text:
            # Get all documents with matching Jira ticket ID (case-insensitive)
            results = collection.get(
                where={"$and": [
                    {"jira_ticket_id": {"$ne": ""}},  # Ensure jira_ticket_id exists and is not empty
                    {"$or": [
                        {"jira_ticket_id": jira_ticket_id.upper()},  # Match uppercase
                        {"jira_ticket_id": jira_ticket_id.lower()}   # Match lowercase
                    ]}
                ]},
                limit=limit,
            )
        else:
            # Get embedding model for text search
            model = get_embedding_model()
            
            # Generate embedding for the query
            query_embedding = model.encode(query_text).tolist()
            
            # Query parameters
            query_params = {
                "query_embeddings": [query_embedding],
                "n_results": limit,
                "include": ['metadatas', 'documents', 'distances']
            }
            
            # Add where filter only if Jira ticket ID is provided
            if jira_ticket_id:
                query_params["where"] = {"$and": [
                    {"jira_ticket_id": {"$ne": ""}},  # Ensure jira_ticket_id exists and is not empty
                    {"$or": [
                        {"jira_ticket_id": jira_ticket_id.upper()},  # Match uppercase
                        {"jira_ticket_id": jira_ticket_id.lower()}   # Match lowercase
                    ]}
                ]}
            
            # Query the collection
            results = collection.query(**query_params)
        
        # Defensive fix: if results is a list, convert to empty dict structure
        if isinstance(results, list):
            results = {"ids": [], "metadatas": [], "documents": [], "distances": []}

        # Process results
        issue_responses = []
        if results and len(results["ids"]) > 0:
            logger.info(f"Found  {len(results)} similar issues")
            # Determine if we're processing query results or direct get results
            is_query_result = query_text and "distances" in results
            
            # Extract results, handling both nested and flat array structures
            # Handle both flat and nested lists for ids, metadatas, documents, and distances
            def flatten_if_nested(val):
                return val[0] if isinstance(val, list) and len(val) > 0 and isinstance(val[0], list) else val

            ids = flatten_if_nested(results.get("ids", []))
            ids = results["ids"][0] if isinstance(results["ids"][0], list) else results["ids"]
            metadatas = results["metadatas"][0] if isinstance(results["metadatas"][0], list) else results["metadatas"]
            documents = results["documents"][0] if isinstance(results["documents"][0], list) else results["documents"]
            distances = results.get("distances", [[0.0]])[0] if isinstance(results.get("distances", [[]])[0], list) else [0.0] * len(ids)

            for i, issue_id in enumerate(ids):
                # Defensive fix: skip invalid empty or list ids
                if not isinstance(issue_id, str) or not issue_id:
                    continue
                metadata = metadatas[i]
                # Defensive fix: if metadata is a list, convert to empty dict
                if isinstance(metadata, list):
                    metadata = {}
                document = documents[i]
                # Calculate similarity score - 1.0 for Jira ID matches, distance-based for text search
                if is_query_result:
                    # distances can be a list of floats or a list of lists
                    if isinstance(distances, list) and len(distances) > i:
                        distance = results["distances"][0][i]
                    else:
                        distance = 0.0
                    similarity_score = 1.0 - min(distance / 2, 1.0)
                else:
                    distance = 0.0
                    similarity_score = 1.0  # 1.0 for exact Jira ID matches
                logger.debug(f"Issue ID: {issue_id} | Distance: {distance:.6f} | Similarity: {similarity_score:.6f}")
                
                # Parse received_date if available
                received_date = None
                if metadata.get("msg_received_date"):
                    try:
                        received_date = datetime.fromisoformat(metadata["msg_received_date"])
                    except:
                        pass
                
                # Reconstruct msg_data dictionary
                msg_data = {
                    'subject': metadata.get('msg_subject', ''),
                    'body': metadata.get('msg_body', ''),
                    'sender': metadata.get('msg_sender', ''),
                    'received_date': metadata.get('msg_received_date', ''),
                    'jira_id': metadata.get('msg_jira_id', ''),
                    'jira_url': metadata.get('msg_jira_url', ''),
                    'recipients': metadata.get('recipients', []),
                    'attachments': metadata.get('attachments', [])
                }

                # Create IssueResponse object
                issue_response = IssueResponse(
                    id=issue_id,
                    title=metadata.get("msg_subject") or metadata.get("jira_summary") or metadata.get("jira_ticket_id") or "Unknown Issue",
                    description=document,
                    jira_ticket_id=metadata.get("jira_ticket_id"),
                    jira_data=None,  # We could fetch this if needed
                    sender=metadata.get("msg_sender"),
                    received_date=metadata.get("msg_received_date", "") or metadata.get("created_date", ""),
                    created_at=datetime.now(),
                    updated_at=None,
                    similarity_score=similarity_score,
                    msg_data=msg_data
                )
                
                issue_responses.append(issue_response)
        
        return issue_responses
    
    except Exception as e:
        logger.error(f"Error searching similar issues: {str(e)}")
        return []  # Return empty list instead of None

    # Clear all issues from the ChromaDB collection
def clear_all_issues() -> bool:
    """
    Delete all documents from the 'production_issues' ChromaDB collection.
    Returns True if successful.
    """
    try:
        client = get_vector_db_client()
        collection = client.get_or_create_collection("production_issues")
        collection.delete(where={"id": {"$ne": ""}})  # Delete all documents
        logger.info("All documents deleted from 'production_issues' collection.")
        return True
    except Exception as e:
        logger.error(f"Error clearing all issues from ChromaDB: {str(e)}")
        raise

# Clear all documents from a specific ChromaDB collection
def clear_collection(collection_name: str) -> bool:
    """
    Delete all documents from the specified ChromaDB collection.
    Returns True if successful.
    """
    try:
        client = get_vector_db_client()
        collection = client.get_or_create_collection(collection_name)
        collection.delete(where={"id": {"$ne": ""}})
        logger.info(f"All documents deleted from '{collection_name}' collection.")
        return True
    except Exception as e:
        logger.error(f"Error clearing collection '{collection_name}' from ChromaDB: {str(e)}")
        raise
        raise

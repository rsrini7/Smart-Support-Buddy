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

def add_issue_to_vectordb(msg_data: Dict[str, Any] = None, jira_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Add a production issue to the vector database.
    
    Args:
        msg_data: Parsed MSG file data (optional if jira_data is provided)
        jira_data: Optional Jira ticket data
        
    Returns:
        ID of the created issue
    """
    try:
        # Ensure at least one of msg_data or jira_data is provided
        if not msg_data and not jira_data:
            raise ValueError("Either MSG data or Jira data must be provided")
            
        # Initialize msg_data as empty dict if not provided
        if not msg_data:
            msg_data = {}
        # Get vector DB client
        client = get_vector_db_client()
        
        # Get embedding model
        model = get_embedding_model()
        
        # Create a unique ID for the issue
        issue_id = f"issue_{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.path.basename(msg_data.get('file_path', ''))}"
        
        # Prepare the text to be embedded
        subject = msg_data.get("subject", "")
        body = msg_data.get("body", "")
        
        # Combine with Jira data if available
        jira_summary = ""
        jira_description = ""
        jira_ticket_id = None
        root_cause = ""
        solution = ""
        
        # If we only have Jira data and no MSG data, use Jira summary as subject
        if jira_data and not (subject or body):
            jira_summary = jira_data.get("summary", "")
            subject = jira_summary
            jira_description = jira_data.get("description", "") or ""
            body = jira_description
        
        if jira_data:
            jira_ticket_id = jira_data.get("key")
            jira_summary = jira_data.get("summary", "")
            jira_description = jira_data.get("description", "") or ""
            
            # Extract root cause and solution from Jira data
            from app.services.jira_service import extract_root_cause_solution
            extracted = extract_root_cause_solution(jira_data)
            root_cause = extracted.get("root_cause", "") or ""
            solution = extracted.get("solution", "") or ""
        
        # Create the full text for embedding
        full_text = f"{subject}\n{body}\n{jira_summary}\n{jira_description}\n{root_cause}\n{solution}"
        
        # Generate embedding
        embedding = model.encode(full_text).tolist()
        
        # Get or create the collection
        collection = client.get_or_create_collection("production_issues")
        
        # Add the document to the collection
        metadata = {
            "subject": subject,
            "sender": msg_data.get("sender", ""),
            "received_date": msg_data.get("received_date", "").isoformat() if msg_data.get("received_date") else "",
            "jira_ticket_id": jira_ticket_id or "",
            "root_cause": root_cause,
            "solution": solution,
            "msg_file_path": msg_data.get("file_path", ""),
            # Add current date if no received_date from MSG
            "created_date": datetime.now().isoformat() if not msg_data.get("received_date") else ""
        }
        
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
        return IssueResponse(
            id=issue_id,
            title=metadata.get('subject', ''),
            description=document,
            root_cause=metadata.get('root_cause', ''),
            solution=metadata.get('solution', ''),
            jira_ticket_id=metadata.get('jira_ticket_id', ''),
            received_date=metadata.get('received_date', '') or metadata.get('created_date', ''),
            created_at=datetime.now(),  # Add required created_at field
            updated_at=None,
            msg_data={
                'subject': metadata.get('subject', ''),
                'sender': metadata.get('sender', ''),
                'file_path': metadata.get('msg_file_path', '')
            } if metadata.get('msg_file_path') else None
        )
        
    except Exception as e:
        logger.error(f"Error getting issue from vector database: {str(e)}")
        raise

def search_similar_issues(query_text: str = "", jira_ticket_id: Optional[str] = None, limit: int = 10) -> List[IssueResponse]:
    """
    Search for similar production issues based on a query text or Jira ticket ID.
    
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
            # Get all documents with matching Jira ticket ID
            results = collection.get(
                where={"jira_ticket_id": jira_ticket_id},
                limit=limit,
            )
        else:
            # Get embedding model for text search
            model = get_embedding_model()
            
            # Generate embedding for the query
            query_embedding = model.encode(query_text).tolist()
            
            # Prepare filter if Jira ticket ID is provided
            where_filter = {"jira_ticket_id": jira_ticket_id} if jira_ticket_id else None
            
            # Query the collection
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_filter,
                include=['metadatas', 'documents', 'distances']
            )
        
        # Process results
        issue_responses = []
        if results and len(results["ids"]) > 0:
            # Determine if we're processing query results or direct get results
            is_query_result = query_text and "distances" in results
            
            # Get the correct indices based on result type
            ids = results["ids"][0] if is_query_result else results["ids"]
            metadatas = results["metadatas"][0] if is_query_result else results["metadatas"]
            documents = results["documents"][0] if is_query_result else results["documents"]
            
            for i, issue_id in enumerate(ids):
                metadata = metadatas[i]
                document = documents[i]
                # Calculate similarity score - 1.0 for Jira ID matches, distance-based for text search
                distance = results["distances"][0][i] if is_query_result else 0.0
                similarity_score = 1.0 - min(distance, 1.0) if is_query_result else 1.0
                
                # Parse received_date if available
                received_date = None
                if metadata.get("received_date"):
                    try:
                        received_date = datetime.fromisoformat(metadata["received_date"])
                    except:
                        pass
                
                # Create IssueResponse object
                issue_response = IssueResponse(
                    id=issue_id,
                    title=metadata.get("subject", "Unknown Issue"),
                    description=document,
                    msg_file_path=metadata.get("msg_file_path"),
                    jira_ticket_id=metadata.get("jira_ticket_id"),
                    jira_data=None,  # We could fetch this if needed
                    sender=metadata.get("sender"),
                    received_date=received_date,
                    created_at=datetime.now(),
                    updated_at=None,
                    root_cause=metadata.get("root_cause"),
                    solution=metadata.get("solution"),
                    similarity_score=similarity_score
                )
                
                issue_responses.append(issue_response)
        
        return issue_responses
    
    except Exception as e:
        logger.error(f"Error searching similar issues: {str(e)}")
        raise
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any
import os
import logging


from app.core.config import settings
from app.services.msg_parser import parse_msg_file
from app.services.jira_service import get_jira_ticket
from app.services.vector_service import search_similar_issues, add_issue_to_vectordb, delete_issue
from app.db.models import IssueCreate, IssueResponse, SearchQuery
from pydantic import BaseModel

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter()

# Import Confluence service
from app.services.confluence_service import (
    add_confluence_page_to_vectordb,
    search_similar_confluence_pages
)

# Import Stack Overflow service
from app.services.stackoverflow_service import (
    add_stackoverflow_qa_to_vectordb,
    search_similar_stackoverflow_content
)

class ConfluenceIngestRequest(BaseModel):
    confluence_url: str

class ConfluenceSearchRequest(BaseModel):
    query_text: str
    limit: int = 10
class StackOverflowIngestRequest(BaseModel):
    stackoverflow_url: str

class StackOverflowSearchRequest(BaseModel):
    query_text: str
    limit: int = 10

@router.get("/jira-ticket/{ticket_id}", response_model=Dict[str, Any])
async def get_jira_ticket_info(ticket_id: str):
    """Get information about a Jira ticket"""
    try:
        jira_data = get_jira_ticket(ticket_id)
        if not jira_data:
            raise HTTPException(status_code=404, detail=f"Jira ticket {ticket_id} not found")
        
        return {
            "status": "success",
            "jira_data": jira_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest-confluence", response_model=Dict[str, Any])
async def ingest_confluence_page(payload: ConfluenceIngestRequest):
    """
    Ingest a Confluence page by URL and store its embedding in the vector DB.
    """
    try:
        page_id = add_confluence_page_to_vectordb(payload.confluence_url)
        if not page_id:
            raise HTTPException(status_code=500, detail="Failed to ingest Confluence page")
        return {
            "status": "success",
            "message": "Confluence page ingested successfully",
            "page_id": page_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.post("/ingest-stackoverflow", response_model=Dict[str, Any])
async def ingest_stackoverflow_qa(payload: StackOverflowIngestRequest):
    """
    Ingest a Stack Overflow Q&A by URL and store its embedding in the vector DB.
    """
    try:
        ids = add_stackoverflow_qa_to_vectordb(payload.stackoverflow_url)
        if not ids:
            raise HTTPException(status_code=500, detail="Failed to ingest Stack Overflow Q&A")
        return {
            "status": "success",
            "message": "Stack Overflow Q&A ingested successfully",
            "ids": ids
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search-stackoverflow", response_model=Dict[str, Any])
async def search_stackoverflow_qa(payload: StackOverflowSearchRequest):
    """
    Search for similar Stack Overflow Q&A based on a query.
    """
    try:
        results = search_similar_stackoverflow_content(payload.query_text, payload.limit)
        if not results or not results.get("ids"):
            return {
                "status": "success",
                "results": []
            }
        # Format results for frontend
        formatted = []
        ids = results["ids"][0] if "distances" in results and results["distances"] else results["ids"]
        metadatas = results["metadatas"][0] if "distances" in results and results["distances"] else results["metadatas"]
        documents = results["documents"][0] if "distances" in results and results["distances"] else results["documents"]
        distances = results["distances"][0] if "distances" in results and results["distances"] else [0.0] * len(ids)
        for i, item_id in enumerate(ids):
            metadata = metadatas[i]
            document = documents[i]
            distance = distances[i]
            similarity_score = 1.0 - min(distance / 2, 1.0)
            formatted.append({
                "item_id": item_id,
                "title": metadata.get("title", "Stack Overflow Q/A"),
                "content": document,
                "similarity_score": similarity_score,
                "metadata": metadata
            })
        return {
            "status": "success",
            "results": formatted
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search-confluence", response_model=Dict[str, Any])
async def search_confluence_pages(payload: ConfluenceSearchRequest):
    """
    Search for similar Confluence pages based on a query.
    """
    try:
        results = search_similar_confluence_pages(payload.query_text, payload.limit)
        if not results or not results.get("ids"):
            return {
                "status": "success",
                "results": []
            }
        # Format results for frontend
        formatted = []
        ids = results["ids"][0] if "distances" in results and results["distances"] else results["ids"]
        metadatas = results["metadatas"][0] if "distances" in results and results["distances"] else results["metadatas"]
        documents = results["documents"][0] if "distances" in results and results["distances"] else results["documents"]
        distances = results["distances"][0] if "distances" in results and results["distances"] else [0.0] * len(ids)
        for i, page_id in enumerate(ids):
            metadata = metadatas[i]
            document = documents[i]
            distance = distances[i]
            similarity_score = 1.0 - min(distance / 2, 1.0)
            formatted.append({
                "page_id": page_id,
                "title": metadata.get("confluence_url", "Confluence Page"),
                "content": document,
                "similarity_score": similarity_score,
                "metadata": metadata
            })
        return {
            "status": "success",
            "results": formatted
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", response_model=List[IssueResponse])
async def search_issues(query: SearchQuery):
    """Search for similar support issues / queries based on a query"""
    try:
        results = search_similar_issues(query.query_text, query.jira_ticket_id, query.limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/issues", response_model=List[IssueResponse])
async def list_issues(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """List all stored support issues / queries with pagination"""
    try:
        # This would be implemented to fetch issues from the database
        # For now, return a placeholder
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/issues/{issue_id}", response_model=IssueResponse)
async def get_issue(issue_id: str):
    """Get a specific production issue by ID"""
    try:
        from app.services.vector_service import get_issue
        issue = get_issue(issue_id)
        if not issue:
            raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
        return issue
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/chroma-clear")
async def clear_chroma_db():
    """
    Delete all data from the ChromaDB 'production_issues' collection.
    """
    from app.services.vector_service import clear_all_issues
    try:
        clear_all_issues()
        return {"status": "success", "message": "All ChromaDB data cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear ChromaDB: {str(e)}")

@router.delete("/chroma-clear/{collection_name}")
async def clear_chroma_collection(collection_name: str):
    """
    Delete all data from the specified ChromaDB collection.
    """
    from app.services.vector_service import clear_collection
    try:
        clear_collection(collection_name)
        return {"status": "success", "message": f"All data cleared from collection '{collection_name}'."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear collection '{collection_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear ChromaDB: {str(e)}")

@router.delete("/issues/{issue_id}")
async def delete_production_issue(issue_id: str):
    """Delete a production issue"""
    try:
        success = delete_issue(issue_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found or could not be deleted")
        
        return {"status": "success", "message": f"Issue {issue_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class IngestDirRequest(BaseModel):
    directory_path: str

@router.post("/ingest-msg-dir", response_model=Dict[str, Any])
async def ingest_msg_directory(payload: IngestDirRequest):
    """
    Ingest all .msg files from a directory path.
    """
    import glob
    import traceback

    directory_path = payload.directory_path

    directory_path = os.path.expanduser(directory_path)
    logger.info(f"Ingesting directory: {directory_path}")
    if not directory_path or not os.path.isdir(directory_path):
        raise HTTPException(status_code=400, detail="Invalid directory path")

    msg_files = glob.glob(os.path.join(directory_path, "*.msg"))
    logger.info(f"Found {len(msg_files)}")
    results = []
    for file_path in msg_files:
        try:
            logger.info(f"Parsing file: {file_path}")
            msg_data = parse_msg_file(file_path)
            issue_id = add_issue_to_vectordb(msg_data=msg_data)
            logger.info(f"Ingested file: {file_path}, issue_id: {issue_id}")
            results.append({"file": file_path, "status": "success", "issue_id": issue_id})
        except Exception as e:
            results.append({"file": file_path, "status": "error", "error": str(e), "traceback": traceback.format_exc()})
            continue

    return {"status": "completed", "total_files": len(msg_files), "results": results}
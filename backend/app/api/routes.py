from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from app.services.vector_service import get_issue as get_issue_from_service
from typing import List, Dict, Any
import os
import logging
from pydantic import BaseModel
import tempfile
from fastapi import Body

from app.core.config import settings
from app.services.msg_parser import parse_msg_file
from app.services.jira_service import get_jira_ticket
from app.services.vector_service import add_issue_to_vectordb, delete_issue, get_all_chroma_collections_data
from app.models import  IssueResponse, SearchQuery
from pydantic import BaseModel
from app.services.vector_service import clear_collection

from app.services.confluence_service import (
    add_confluence_page_to_vectordb,
    search_similar_confluence_pages
)

from app.services.stackoverflow_service import (
    add_stackoverflow_qa_to_vectordb,
    search_similar_stackoverflow_content
)


class JiraIngestRequest(BaseModel):
    jira_ticket_ids: List[str]

class IngestDirRequest(BaseModel):
    directory_path: str

class SimilarityThresholdRequest(BaseModel):
    similarity_threshold: float

class ConfluenceIngestRequest(BaseModel):
    confluence_urls: List[str]

class ConfluenceSearchRequest(BaseModel):
    query_text: str
    limit: int = 10
class StackOverflowIngestRequest(BaseModel):
    stackoverflow_urls: List[str]

class StackOverflowSearchRequest(BaseModel):
    query_text: str
    limit: int = 10


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter()

@router.get("/config/similarity-threshold")
async def get_similarity_threshold():
    """
    Get the current similarity threshold (user-set or fallback).
    """
    return {"similarity_threshold": settings.SIMILARITY_THRESHOLD}

@router.post("/config/similarity-threshold")
async def set_similarity_threshold(payload: SimilarityThresholdRequest = Body(...)):
    """
    Set a new similarity threshold (persists to config file).
    """
    try:
        value = float(payload.similarity_threshold)
        if not (0.0 < value < 1.0):
            raise HTTPException(status_code=400, detail="similarity_threshold must be between 0 and 1 (exclusive)")
        settings.set_similarity_threshold(value)
        return {"status": "success", "similarity_threshold": value}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid value: {e}")

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
    Ingest multiple Confluence pages by URL and store their embeddings in the vector DB.
    """
    results = []
    for url in payload.confluence_urls:
        try:
            page_id = add_confluence_page_to_vectordb(url)
            if not page_id:
                results.append({
                    "confluence_url": url,
                    "status": "error",
                    "message": "Failed to ingest Confluence page"
                })
                continue
            results.append({
                "confluence_url": url,
                "status": "success",
                "message": "Confluence page ingested successfully",
                "page_id": page_id
            })
        except Exception as e:
            results.append({
                "confluence_url": url,
                "status": "error",
                "message": str(e)
            })
    return {
        "results": results
    }
    
@router.post("/ingest-stackoverflow", response_model=Dict[str, Any])
async def ingest_stackoverflow_qa(payload: StackOverflowIngestRequest):
    """
    Ingest multiple Stack Overflow Q&A by URL and store their embeddings in the vector DB.
    """
    results = []
    for url in payload.stackoverflow_urls:
        try:
            ids = add_stackoverflow_qa_to_vectordb(url)
            if not ids:
                results.append({
                    "stackoverflow_url": url,
                    "status": "error",
                    "message": "Failed to ingest Stack Overflow Q&A"
                })
                continue
            results.append({
                "stackoverflow_url": url,
                "status": "success",
                "message": "Stack Overflow Q&A ingested successfully",
                "ids": ids
            })
        except Exception as e:
            results.append({
                "stackoverflow_url": url,
                "status": "error",
                "message": str(e)
            })
    return {
        "results": results
    }

@router.post("/ingest-jira", response_model=Dict[str, Any])
async def ingest_jira_ticket(payload: JiraIngestRequest):
    """
    Ingest multiple Jira tickets by ID and embed them into the Chroma vector database.
    """
    from app.services.jira_service import get_jira_ticket
    from app.services.vector_service import add_issue_to_vectordb

    results = []
    for jira_id in payload.jira_ticket_ids:
        try:
            jira_data = get_jira_ticket(jira_id)
            if not jira_data:
                results.append({
                    "jira_ticket_id": jira_id,
                    "status": "error",
                    "message": f"Jira ticket {jira_id} not found or could not be fetched"
                })
                continue
            issue_id = add_issue_to_vectordb(jira_data=jira_data)
            results.append({
                "jira_ticket_id": jira_id,
                "status": "success",
                "message": f"Jira ticket {jira_id} ingested successfully",
                "issue_id": issue_id,
                "jira_data": jira_data
            })
        except Exception as e:
            results.append({
                "jira_ticket_id": jira_id,
                "status": "error",
                "message": str(e)
            })
    return {
        "results": results
    }

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
            if similarity_score == 0.0:
                continue  # Skip results with 0.00% similarity
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
        seen = set()
        for i, page_id in enumerate(ids):
            metadata = metadatas[i]
            document = documents[i]
            confluence_url = metadata.get("confluence_url", "")
            unique_key = (str(page_id), confluence_url, document)
            if unique_key in seen:
                continue
            seen.add(unique_key)
            distance = distances[i]
            similarity_score = 1.0 - min(distance / 2, 1.0)
            if similarity_score == 0.0:
                continue  # Skip results with 0.00% similarity
            formatted.append({
                "page_id": page_id,
                "title": confluence_url or "Confluence Page",
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

@router.post("/search")
async def search_issues(query: SearchQuery):
    """
    Search for similar support issues / queries across vector DB, Confluence, and Stack Overflow in parallel.
    Returns a dict with results from all sources.
    """
    import asyncio
    from app.services.vector_service import search_similar_issues
    from app.services.confluence_service import search_similar_confluence_pages
    from app.services.stackoverflow_service import search_similar_stackoverflow_content

    try:
        vector_task = asyncio.to_thread(search_similar_issues, query.query_text, query.jira_ticket_id, query.limit)
        confluence_task = asyncio.to_thread(search_similar_confluence_pages, query.query_text, query.limit)
        stackoverflow_task = asyncio.to_thread(search_similar_stackoverflow_content, query.query_text, query.limit)

        vector_issues, confluence_results, stackoverflow_results = await asyncio.gather(
            vector_task, confluence_task, stackoverflow_task
        )

        # Defensive: ensure no NoneType for iterables
        if vector_issues is None:
            vector_issues = []
        if confluence_results is None:
            confluence_results = []
        if stackoverflow_results is None:
            stackoverflow_results = []

        # Ensure stackoverflow_results is always a list or a consistent structure
        if isinstance(stackoverflow_results, dict) and "results" in stackoverflow_results:
            stackoverflow_results = stackoverflow_results["results"]

        # Combine all results for single page result
        combined_results = []
        for item in vector_issues:
            if hasattr(item, "dict"):
                item_data = item.dict()
            else:
                item_data = dict(item)
            combined_results.append({
                "type": "vector_issue",
                **item_data,
                "similarity_score": item_data.get("similarity_score", getattr(item, "similarity_score", 0))
            })
        for item in confluence_results:
            combined_results.append({
                "type": "confluence",
                **item,
                "similarity_score": item.get("similarity_score", 0)
            })
        for item in stackoverflow_results:
            combined_results.append({
                "type": "stackoverflow",
                **item,
                "similarity_score": item.get("similarity_score", 0)
            })
        # Sort combined results by similarity_score descending
        combined_results.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)

        return {
            "results": combined_results,
            "vector_issues": vector_issues,
            "confluence_results": confluence_results,
            "stackoverflow_results": stackoverflow_results
        }
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
    """Get a specific RCA by ID"""
    try:
        issue = get_issue_from_service(issue_id)
        if not issue:
            raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
        # If Jira details are unavailable, log a warning but still return the issue details
        if hasattr(issue, "jira_data") and issue.jira_data is None:
            import logging
            logging.warning(f"Jira details unavailable for issue {issue_id}. Returning issue details without Jira data.")
        return issue
    except Exception as e:
        # Only raise 500 for truly fatal errors (not for missing Jira data)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/chroma-clear/{collection_name}")
async def clear_chroma_collection(collection_name: str):
    """
    Delete all data from the specified ChromaDB collection.
    """
    try:
        result = clear_collection(collection_name)
        return {"success": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from app.core.config import settings
from app.services.faiss_client import FaissClient # Add import for FaissClient

@router.get("/chroma-collections")
async def get_chroma_collections():
    """
    Get all vector database collections (ChromaDB or FAISS) and their basic info.
    """
    if settings.USE_FAISS:
        try:
            # Ensure FAISS_INDEX_PATH is configured
            if not settings.FAISS_INDEX_PATH:
                raise HTTPException(status_code=500, detail="FAISS_INDEX_PATH is not configured in settings.")
            faiss_client = FaissClient(base_path=settings.FAISS_INDEX_PATH)
            data = faiss_client.get_collections_with_records()
            logger.info(f"Retrieved FAISS collections: {len(data)}")
        except Exception as e:
            logger.error(f"Error accessing FAISS collections: {e}")
            raise HTTPException(status_code=500, detail=f"Error accessing FAISS collections: {str(e)}")
    else:
        try:
            data = get_all_chroma_collections_data() or []
            if not isinstance(data, list):
                data = []
            logger.info(f"Retrieved ChromaDB collections: {len(data)}")
        except Exception as e:
            logger.error(f"Error accessing ChromaDB collections: {e}")
            raise HTTPException(status_code=500, detail=f"Error accessing ChromaDB collections: {str(e)}")

    return {"collections": data if isinstance(data, list) else []}
    
@router.delete("/issues/{issue_id}")
async def delete_production_issue(issue_id: str):
    """Delete a RCA"""
    try:
        success = delete_issue(issue_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found or could not be deleted")
        
        return {"status": "success", "message": f"Issue {issue_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest-msg-dir")
async def ingest_msg_dir(files: List[UploadFile] = File(...)):
    import traceback
    try:
        logger.info(f"/ingest-msg-dir called. Number of files received: {len(files)}")
        for idx, file in enumerate(files):
            logger.info(f"File {idx}: filename={file.filename}, content_type={file.content_type}")
        with tempfile.TemporaryDirectory() as temp_dir:
            saved_file_paths = []
            for file in files:
                try:
                    file_path = os.path.join(temp_dir, file.filename)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    logger.info(f"Saving uploaded file: {file_path}")
                    with open(file_path, "wb") as f:
                        f.write(await file.read())
                    saved_file_paths.append(file_path)
                except Exception as file_save_err:
                    logger.error(f"Error saving file {file.filename}: {file_save_err}")
                    logger.error(traceback.format_exc())
            results = []
            for file_path in saved_file_paths:
                logger.info(f"Calling parse_msg_file for: {file_path}")
                msg_data = parse_msg_file(file_path)
                if isinstance(msg_data, dict) and msg_data.get("status") == "error":
                    results.append(msg_data)
                    continue
                try:
                    issue_id = add_issue_to_vectordb(msg_data=msg_data)
                    msg_data["issue_id"] = issue_id
                    msg_data["status"] = "success"
                except Exception as e:
                    msg_data["status"] = "error"
                    msg_data["error"] = str(e)
                results.append(msg_data)
            return {"status": "success", "results": results}
    except Exception as e:
        logger.error(f"Error in ingest_msg_dir: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error ingesting MSG files: {str(e)}")
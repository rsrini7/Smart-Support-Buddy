from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import os
import json

from app.core.config import settings
from app.services.msg_parser import parse_msg_file
from app.services.jira_service import get_jira_ticket, link_msg_to_jira
from app.services.vector_service import search_similar_issues, add_issue_to_vectordb, delete_issue
from app.db.models import IssueCreate, IssueResponse, SearchQuery

router = APIRouter()

@router.post("/upload-msg", response_model=Dict[str, Any])
async def upload_msg_file(
    file: Optional[UploadFile] = File(None),
    jira_ticket_id: str = Form(...)
):
    """Upload an MSG file and/or process a Jira ticket. Jira ticket ID is required."""
    try:
        # Initialize variables
        msg_data = {}
        file_path = None
        
        # Get Jira ticket data (required)
        jira_data = get_jira_ticket(jira_ticket_id)
        if not jira_data:
            raise HTTPException(status_code=404, detail=f"Jira ticket {jira_ticket_id} not found")
        
        # Process file if provided
        if file:
            file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            # Parse the MSG file
            msg_data = parse_msg_file(file_path)
            
            # Link MSG data to Jira
            link_msg_to_jira(msg_data, jira_data)
            
        # Add the issue to the vector database
        issue_id = add_issue_to_vectordb(msg_data if file else None, jira_data)
        
        # Customize success message based on what was provided
        message = "MSG file uploaded and linked to Jira ticket successfully" if file else "Jira ticket processed successfully"
        
        return {
            "status": "success",
            "message": message,
            "issue_id": issue_id,
            "msg_data": msg_data,
            "jira_data": jira_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

@router.post("/search", response_model=List[IssueResponse])
async def search_issues(query: SearchQuery):
    """Search for similar production issues based on a query"""
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
    """List all stored production issues with pagination"""
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
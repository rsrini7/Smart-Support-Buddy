from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class IssueCreate(BaseModel):
    """Schema for creating a new RCA"""
    title: str
    description: str
    jira_ticket_id: Optional[str] = None
    sender: Optional[str] = None
    received_date: Optional[datetime] = None
    attachments: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class IssueResponse(BaseModel):
    """Schema for returning a RCA"""
    id: str
    title: str
    description: str
    jira_ticket_id: Optional[str] = None
    jira_data: Optional[Dict[str, Any]] = None
    msg_data: Optional[Dict[str, Any]] = None
    sender: Optional[str] = None
    received_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    root_cause: Optional[str] = None
    solution: Optional[str] = None
    similarity_score: Optional[float] = None  # Used in search results

class SearchQuery(BaseModel):
    """Schema for searching support issues / queries"""
    query_text: str
    jira_ticket_id: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)
    use_llm: bool = False  # Add flag for LLM usage

class JiraTicket(BaseModel):
    """Schema for Jira ticket data"""
    id: str
    key: str
    summary: str
    description: Optional[str] = None
    status: str
    created: datetime
    updated: datetime
    assignee: Optional[str] = None
    reporter: Optional[str] = None
    priority: Optional[str] = None
    resolution: Optional[str] = None
    components: Optional[List[str]] = None
    labels: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None

class MsgFile(BaseModel):
    """Schema for MSG file data"""
    file_path: str
    subject: str
    sender: str
    recipients: List[str]
    body: str
    received_date: datetime
    attachments: Optional[List[str]] = None
    headers: Optional[Dict[str, str]] = None
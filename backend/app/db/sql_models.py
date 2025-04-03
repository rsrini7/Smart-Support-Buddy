from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Issue(Base):
    """SQL model for production issues"""
    __tablename__ = "issues"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    msg_file_path = Column(String, nullable=True)
    jira_ticket_id = Column(String, nullable=True, index=True)
    sender = Column(String, nullable=True)
    received_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    root_cause = Column(Text, nullable=True)
    solution = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Relationship with JiraTicket if needed
    # jira_ticket = relationship("JiraTicket", back_populates="issues")

class JiraTicketData(Base):
    """SQL model for Jira ticket data"""
    __tablename__ = "jira_tickets"
    
    id = Column(String, primary_key=True)
    key = Column(String, nullable=False, index=True, unique=True)
    summary = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False)
    created = Column(DateTime, nullable=False)
    updated = Column(DateTime, nullable=False)
    assignee = Column(String, nullable=True)
    reporter = Column(String, nullable=True)
    priority = Column(String, nullable=True)
    resolution = Column(String, nullable=True)
    components = Column(JSON, nullable=True)  # List of components
    labels = Column(JSON, nullable=True)  # List of labels
    custom_fields = Column(JSON, nullable=True)  # Custom fields
    
    # Relationship with Issue if needed
    # issues = relationship("Issue", back_populates="jira_ticket")

class VectorEmbedding(Base):
    """SQL model for vector embeddings of issues"""
    __tablename__ = "vector_embeddings"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    issue_id = Column(String, ForeignKey("issues.id"), nullable=False)
    embedding_type = Column(String, nullable=False)  # e.g., "description", "solution"
    # Note: The actual vector embeddings would be stored in the vector database
    # This table maintains the mapping between issues and their embeddings
    vector_id = Column(String, nullable=False)  # ID in the vector database
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationship with Issue
    issue = relationship("Issue")
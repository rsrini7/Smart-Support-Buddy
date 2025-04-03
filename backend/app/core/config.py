import os
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Production Issue Identifier"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:9000"]
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/prodissue")
    
    # Jira settings
    JIRA_URL: Optional[str] = os.getenv("JIRA_URL")
    JIRA_USERNAME: Optional[str] = os.getenv("JIRA_USERNAME")
    JIRA_API_TOKEN: Optional[str] = os.getenv("JIRA_API_TOKEN")
    
    # Vector DB settings
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "./data/vectordb")
    
    # File storage settings
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./data/uploads")
    
    # LLM settings
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    
    class Config:
        case_sensitive = True

# Create settings instance
settings = Settings()

# Ensure required directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.VECTOR_DB_PATH, exist_ok=True)
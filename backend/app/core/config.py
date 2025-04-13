import os
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

env_loaded = load_dotenv('.env')
if env_loaded:
    logger.info("Loaded environment variables from .env")
else:
    logger.warning("No environment file (.env) found, using default values")

class Settings(BaseSettings):
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Support Buddy"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:9000"]
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/prodissue")
    
    # Jira settings
    JIRA_URL: str = os.getenv("JIRA_URL", "http://localhost:9090")
    JIRA_USERNAME: str = os.getenv("JIRA_USERNAME", "admin")
    JIRA_API_TOKEN: str = os.getenv("JIRA_API_TOKEN", "")
    JIRA_PASSWORD: str = os.getenv("JIRA_PASSWORD", "")  # For local Jira instance authentication
    
    @property
    def has_valid_jira_config(self) -> bool:
        """Check if Jira configuration is valid."""
        return bool(self.JIRA_URL and self.JIRA_USERNAME and (self.JIRA_API_TOKEN or self.JIRA_PASSWORD))
    
    # Vector DB settings
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "./data/vectordb")
    
    # File storage settings
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./data/uploads")
    
    # LLM settings
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", 0.1))


    class Config:
        case_sensitive = True

# Create settings instance
settings = Settings()

# Ensure required directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.VECTOR_DB_PATH, exist_ok=True)
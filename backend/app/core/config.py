import os
from pydantic_settings import BaseSettings
from typing import Optional, List
from dotenv import load_dotenv
import logging
import json

logger = logging.getLogger(__name__)

env_loaded = load_dotenv('.env')
if env_loaded:
    logger.info("Loaded environment variables from .env")
else:
    logger.warning("No environment file (.env) found, using default values")

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

def read_config_value_from_file(key: str):
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                data = json.load(f)
                value = data.get(key)
                if value is not None:
                    return value
    except Exception as e:
        logger.warning(f"Could not read {key} from config file: {e}")
    return None

def write_config_value_to_file(key: str, value):
    try:
        data = {}
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                data = json.load(f)
        data[key] = value
        with open(CONFIG_PATH, "w") as f:
            json.dump(data, f)
    except Exception as e:
        logger.error(f"Could not write {key} to config file: {e}")

class Settings(BaseSettings):
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Support Buddy"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:9000"]
    
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
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "./data/chroma")
    CHROMA_USE_HTTP: bool = os.getenv("CHROMA_USE_HTTP", "false").lower() == "true"
    USE_FAISS: bool = os.getenv("USE_FAISS", "false").lower() == "true"
    FAISS_INDEX_PATH: str = os.getenv("FAISS_INDEX_PATH", "./data/faiss")
    
    # OpenRouter LLM API settings
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_API_URL: str = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "openai/gpt-3.5-turbo")
    YOUR_SITE_URL: str = os.getenv("YOUR_SITE_URL", "http://localhost:3000")
    YOUR_APP_NAME: str = os.getenv("YOUR_APP_NAME", "SupportBuddy")
    
    # LLM settings
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    MODEL_LOCAL_PATH: Optional[str] = os.getenv("MODEL_LOCAL_PATH", None)
    _SIMILARITY_THRESHOLD_ENV: float = float(os.getenv("SIMILARITY_THRESHOLD", 0.1))
    _LLM_TOP_RESULTS_COUNT_ENV: int = int(os.getenv("LLM_TOP_RESULTS_COUNT", 3))

    @property
    def SIMILARITY_THRESHOLD(self) -> float:
        """Return the user-set similarity threshold if present, else fallback to env/default."""
        file_value = read_config_value_from_file("SIMILARITY_THRESHOLD")
        if file_value is not None:
            return float(file_value)
        return self._SIMILARITY_THRESHOLD_ENV

    @property
    def LLM_TOP_RESULTS(self) -> int:
        """Return the user-set LLM top results count if present, else fallback to env/default."""
        file_value = read_config_value_from_file("LLM_TOP_RESULTS_COUNT")
        if file_value is not None:
            return int(file_value)
        return self._LLM_TOP_RESULTS_COUNT_ENV

    def set_similarity_threshold(self, value: float):
        write_config_value_to_file("SIMILARITY_THRESHOLD", value)

    def set_llm_top_results_count(self, value: int):
        write_config_value_to_file("LLM_TOP_RESULTS_COUNT", value)

    class Config:
        case_sensitive = True

# Create settings instance
settings = Settings()

# Ensure required directories exist
os.makedirs(settings.VECTOR_DB_PATH, exist_ok=True)
if settings.USE_FAISS:
    os.makedirs(settings.FAISS_INDEX_PATH, exist_ok=True)
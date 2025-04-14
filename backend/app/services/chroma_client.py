import chromadb
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

def get_vector_db_client():
    """
    Get a ChromaDB client instance.
    Returns:
        ChromaDB client instance
    """
    try:
        chromadb.configure(anonymized_telemetry=False)
        client = chromadb.PersistentClient(path=settings.VECTOR_DB_PATH)
        return client
    except Exception as e:
        logger.error(f"Error initializing vector database client: {str(e)}")
        raise

def get_collection(collection_name: str):
    client = get_vector_db_client()
    return client.get_or_create_collection(collection_name)

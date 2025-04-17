import chromadb
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

def get_vector_db_client(db_path: str = None):
    """
    Returns a ChromaDB PersistentClient. Uses settings.VECTOR_DB_PATH if db_path is not provided.
    """
    try:
        chromadb.configure(anonymized_telemetry=False)
        client = chromadb.PersistentClient(path=db_path or settings.VECTOR_DB_PATH)
        return client
    except Exception as e:
        logger.error(f"Error initializing vector database client: {str(e)}")
        raise

def get_collection(collection_name: str):
    client = get_vector_db_client()
    return client.get_or_create_collection(collection_name)


def clear_collection(collection_name: str) -> bool:
    try:
        collection = get_collection(collection_name)
        collection.delete(where={"id": {"$ne": ""}})
        logger.info(f"All documents deleted from '{collection_name}' collection.")
        return True
    except Exception as e:
        logger.error(f"Error clearing collection '{collection_name}' from ChromaDB: {str(e)}")
        raise

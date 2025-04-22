import chromadb
import logging
import os
from app.core.config import settings
from chromadb.config import Settings

logger = logging.getLogger(__name__)

def get_vector_db_client(db_path: str = None):
    """
    Returns a ChromaDB PersistentClient (ChromaDB 0.4.x+).
    Uses settings.VECTOR_DB_PATH if db_path is not provided.
    Logs the persist directory and current working directory for debugging.
    """
    try:
        persist_dir = db_path or settings.VECTOR_DB_PATH
        logger.debug(f"ChromaDB Persist Directory: {persist_dir}")
        logger.debug(f"Current Working Directory: {os.getcwd()}")
        client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(
                anonymized_telemetry=False,
            )
        )
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

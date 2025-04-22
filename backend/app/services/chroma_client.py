import chromadb
import logging
import os
from app.core.config import settings
from chromadb.config import Settings

logger = logging.getLogger(__name__)

def get_vector_db_client(db_path: str = None):
    """
    Returns a ChromaDB PersistentClient (ChromaDB 0.4.x+) or HttpClient if USE_HTTP is true.
    Uses settings.VECTOR_DB_PATH if db_path is not provided.
    Logs the persist directory and current working directory for debugging.
    """
    try:
        use_http = os.getenv("CHROMA_USE_HTTP", "false").lower() == "true"
        if use_http:
            # Default to localhost:8000, can be extended to support env config
            logger.info("Using ChromaDB HttpClient (server mode)")
            client = chromadb.HttpClient(
                host="localhost",
                port=8000,
                settings=Settings(anonymized_telemetry=False)
            )
            return client
        
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

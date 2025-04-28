import chromadb
import logging
import os
from app.core.config import settings
from chromadb.config import Settings

logger = logging.getLogger(__name__)

_vector_db_client = None # Global cache for the client

def get_vector_db_client(db_path: str = None):
    """
    Returns a ChromaDB PersistentClient (ChromaDB 0.4.x+) or HttpClient if CHROMA_USE_HTTP is true,
    OR a FaissClient if USE_FAISS is true.
    Uses settings.VECTOR_DB_PATH or settings.FAISS_INDEX_PATH based on the chosen client.
    Logs the persist directory and current working directory for debugging.
    Caches the client instance.
    """
    global _vector_db_client
    if _vector_db_client is not None:
        return _vector_db_client

    try:
        use_faiss = os.getenv("USE_FAISS", "false").lower() == "true"

        if use_faiss:
            logger.info("Using FAISS client.")
            from app.services.faiss_client import FaissClient # Import locally to avoid circular dependency if FaissClient uses settings
            faiss_path = settings.FAISS_INDEX_PATH
            logger.debug(f"FAISS Base Path: {faiss_path}")
            _vector_db_client = FaissClient(base_path=faiss_path)
            return _vector_db_client
        else:
            chroma_use_http = os.getenv("CHROMA_USE_HTTP", "false").lower() == "true"
            if chroma_use_http:
                # Default to localhost:8000, can be extended to support env config
                logger.info("Using ChromaDB HttpClient (server mode)")
                _vector_db_client = chromadb.HttpClient(
                    host="localhost",
                    port=8000,
                    settings=Settings(anonymized_telemetry=False)
                )
                return _vector_db_client
            else:
                persist_dir = db_path or settings.VECTOR_DB_PATH
                logger.info(f"Using ChromaDB PersistentClient. Path: {persist_dir}")
                logger.debug(f"Current Working Directory: {os.getcwd()}")
                _vector_db_client = chromadb.PersistentClient(
                    path=persist_dir,
                    settings=Settings(
                        anonymized_telemetry=False,
                    )
                )
                return _vector_db_client
    except Exception as e:
        logger.error(f"Error initializing vector database client: {str(e)}")
        raise

def get_collection(collection_name: str):
    """
    Gets or creates a collection from the configured vector database (ChromaDB or FAISS).
    If collection does not exist, it will be created.
    """
    client = get_vector_db_client()
    # Try to get or create the collection, robust to non-existence
    try:
        # Many Chroma/FAISS clients support get_or_create_collection, but fallback if not
        if hasattr(client, 'get_or_create_collection'):
            return client.get_or_create_collection(collection_name)
        elif hasattr(client, 'get_collection') and hasattr(client, 'create_collection'):
            try:
                return client.get_collection(collection_name)
            except Exception:
                return client.create_collection(collection_name)
        else:
            raise RuntimeError("Vector DB client does not support collection creation.")
    except Exception as e:
        # Last resort: try to create the collection
        if hasattr(client, 'create_collection'):
            return client.create_collection(collection_name)
        raise

def clear_collection(collection_name: str) -> bool:
    """
    Clears a collection. Note: FAISS implementation might differ.
    For FAISS, this might mean deleting and recreating the collection files.
    """
    try:
        client = get_vector_db_client()
        use_faiss = os.getenv("USE_FAISS", "false").lower() == "true"

        if use_faiss:
            collection = client.get_collection(collection_name)
            if collection is not None and hasattr(collection, "clear"):
                collection.clear()
                logger.info(f"FAISS collection '{collection_name}' cleared using clear().")
            else:
                logger.warning(f"FAISS collection '{collection_name}' not found or does not support clear(). Deleting and recreating.")
                client.delete_collection(collection_name)
                client.get_or_create_collection(collection_name) # Recreate it empty
                logger.info(f"FAISS collection '{collection_name}' deleted and recreated.")
            return True
        else:
            # ChromaDB's way
            try:
                # Attempt to get the collection first
                collection = client.get_collection(collection_name)
                count = collection.count()
                if count > 0:
                    logger.info(f"Clearing Index collection '{collection_name}' which has {count} items.")
                    # Index's delete method with filter is preferred if available and works
                    # Using a simple filter that should match all items
                    collection.delete(where={})
                    logger.info(f"Index collection '{collection_name}' cleared using delete with filter.")
                else:
                    logger.info(f"Index collection '{collection_name}' is already empty.")
            except Exception as get_err:
                 # Handle case where collection might not exist or other errors during get/delete
                 logger.warning(f"Could not get or clear Index data '{collection_name}': {get_err}. It might not exist.")
                 # Optionally, try deleting the collection entirely if clearing fails
                 try:
                     client.delete_collection(collection_name)
                     logger.info(f"Deleted Index collection '{collection_name}' as fallback.")
                     client.create_collection(collection_name) # Recreate empty
                 except Exception as del_err:
                     logger.error(f"Failed to delete and recreate ChromaDB collection '{collection_name}': {del_err}")
            return True
    except Exception as e:
        logger.error(f"Error clearing collection '{collection_name}': {str(e)}")
        raise

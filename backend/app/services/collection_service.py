from app.services.chroma_client import get_collection
import logging

logger = logging.getLogger(__name__)

def clear_all_issues() -> bool:
    try:
        collection = get_collection("production_issues")
        collection.delete(where={"id": {"$ne": ""}})
        logger.info("All documents deleted from 'production_issues' collection.")
        return True
    except Exception as e:
        logger.error(f"Error clearing all issues from ChromaDB: {str(e)}")
        raise

def clear_collection(collection_name: str) -> bool:
    try:
        collection = get_collection(collection_name)
        collection.delete(where={"id": {"$ne": ""}})
        logger.info(f"All documents deleted from '{collection_name}' collection.")
        return True
    except Exception as e:
        logger.error(f"Error clearing collection '{collection_name}' from ChromaDB: {str(e)}")
        raise

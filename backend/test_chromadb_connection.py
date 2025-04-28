import logging
from app.services.chroma_client import get_vector_db_client, get_collection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_connection():
    try:
        # Get client using existing implementation
        client = get_vector_db_client()
        logger.info("Successfully got ChromaDB client")
        
        # Test collection operations
        collection = get_collection("test_collection")
        logger.info(f"Working with collection: {collection.name}")
        
        # Test basic operations
        collection.add(
            documents=["test document"],
            ids=["test_id"]
        )
        results = collection.query(query_texts=["test document"], n_results=1)
        logger.info("Successfully performed basic collection operations")
        logger.info(f"Query results: {results}")
        return True
        
    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()
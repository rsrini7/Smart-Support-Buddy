from sentence_transformers import SentenceTransformer
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

_model_instance = None

def get_embedding_model():
    """
    Singleton loader for the sentence transformer embedding model.
    Returns:
        SentenceTransformer model instance
    """
    global _model_instance
    if _model_instance is None:
        try:
            _model_instance = SentenceTransformer(settings.EMBEDDING_MODEL)
        except Exception as e:
            logger.error(f"Error initializing embedding model: {str(e)}")
            raise
    return _model_instance

def get_embedding(text: str):
    model = get_embedding_model()
    return model.encode(text).tolist()

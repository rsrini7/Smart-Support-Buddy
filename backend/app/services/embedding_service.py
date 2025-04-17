from sentence_transformers import SentenceTransformer
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

_model_instance = None

def get_embedding_model(embedding_model: str = None, device: str = 'cpu'):
    """
    Singleton loader for the sentence transformer embedding model.
    Returns:
        SentenceTransformer model instance
    """
    global _model_instance
    if _model_instance is None:
        try:
            # Always load on CPU
            _model_instance = SentenceTransformer(embedding_model or settings.EMBEDDING_MODEL, device=device)
        except Exception as e:
            logger.error(f"Error initializing embedding model: {str(e)}")
            raise
    return _model_instance

def get_embedding(text: str):
    model = get_embedding_model()
    return model.encode(text).tolist()

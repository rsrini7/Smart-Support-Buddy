from sentence_transformers import SentenceTransformer
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

_model_instance = None

def get_embedding_model(embedding_model: str = None, device: str = 'cpu', model_path: str = None):
    """
    Singleton loader for the sentence transformer embedding model.
    If model_path is provided, loads model from the local folder.
    Returns:
        SentenceTransformer model instance
    """
    global _model_instance
    if _model_instance is None:
        try:
            # Always load on CPU
            # Use model_path from argument, then from settings, else fallback
            final_model_path = model_path or settings.MODEL_LOCAL_PATH
            if final_model_path:
                _model_instance = SentenceTransformer(final_model_path, device=device)
            else:
                _model_instance = SentenceTransformer(embedding_model or settings.EMBEDDING_MODEL, device=device)
        except Exception as e:
            logger.error(f"Error initializing embedding model: {str(e)}")
            raise
    return _model_instance

def get_embedding(text: str, model_path: str = None):
    model = get_embedding_model(model_path=model_path)
    return model.encode(text).tolist()

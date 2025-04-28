import logging
logger = logging.getLogger(__name__)

import numpy as np

def compute_similarity_score(cosine_similarity: float) -> float:
    """
    Compute the similarity score given a cosine similarity value.
    Args:
        cosine_similarity (float): Cosine similarity between two vectors, typically in [-1, 1]
    Returns:
        float: The similarity score in the range [0.0, 1.0]
    """
    logger.info(f"Cosine similarity: {cosine_similarity}")
    # Map cosine similarity [-1, 1] to [0, 1]
    score = (cosine_similarity + 1) / 2
    return min(max(score, 0), 1)

def compute_text_similarity_score(text1: str, text2: str, embedder=None) -> float:
    """
    Compute the similarity score between two texts using their embeddings (cosine similarity).
    Args:
        text1 (str): First text.
        text2 (str): Second text.
        embedder: SentenceTransformer or similar embedding model (optional, will load if not provided).
    Returns:
        float: Similarity score in [0.0, 1.0]
    """
    from app.services.embedding_service import get_embedding_model
    if embedder is None:
        embedder = get_embedding_model()
    emb1 = embedder.encode([text1])[0]
    emb2 = embedder.encode([text2])[0]
    # Compute cosine similarity
    cosine_sim = float(np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2)))
    return compute_similarity_score(cosine_sim)

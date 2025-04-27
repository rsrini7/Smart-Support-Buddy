import logging
logger = logging.getLogger(__name__)

def compute_similarity_score(distance: float) -> float:
    """
    Compute the similarity score given a distance value.
    The formula is: 1.0 - min(distance / 2, 1.0)
    Args:
        distance (float): The distance value (typically from a vector search or embedding).
    Returns:
        float: The similarity score in the range [0.0, 1.0]
    """
    # return 1.0 - min(distance / 2, 1.0)
    logger.info(f"Distance: {distance}")
    # return math.exp(-distance)
    # return 1 / (1 + math.exp(4 * (distance - 0.5)))  # Sigmoid centered at 0.5

    return min(max(1.0 - distance /2, 0), 1)

def compute_text_similarity_score(text1: str, text2: str, embedder=None) -> float:
    """
    Compute the similarity score between two texts using their embeddings.
    Args:
        text1 (str): First text.
        text2 (str): Second text.
        embedder: SentenceTransformer or similar embedding model (optional, will load if not provided).
    Returns:
        float: Similarity score in [0.0, 1.0]
    """
    from app.services.embedding_service import get_embedding_model
    import numpy as np
    if embedder is None:
        embedder = get_embedding_model()
    emb1 = embedder.encode([text1])[0]
    emb2 = embedder.encode([text2])[0]
    distance = np.linalg.norm(emb1 - emb2)
    return compute_similarity_score(distance)

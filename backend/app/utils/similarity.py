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

from sentence_transformers import CrossEncoder
from functools import lru_cache

@lru_cache(maxsize=2)
def get_reranker(model_name=None):
    # You may customize this logic to use a default model from config if model_name is None
    if model_name is None:
        model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    return CrossEncoder(model_name)

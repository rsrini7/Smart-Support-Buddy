import dspy
from app.core.config import settings

def get_openrouter_llm(max_tokens: int = 500):
    """
    Returns a DSPy LLM instance configured for OpenRouter using environment/config settings.
    Args:
        max_tokens: Maximum tokens for LLM output (default 500)
    Returns:
        dspy.LM instance for OpenRouter
    """
    return dspy.LM(
        model=settings.OPENROUTER_MODEL,
        api_key=settings.OPENROUTER_API_KEY,
        api_base=settings.OPENROUTER_API_URL,
        provider="openrouter",
        max_tokens=max_tokens
    )

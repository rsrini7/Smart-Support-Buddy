import dspy
from typing import Optional, Dict, Any
from app.core.config import settings
from app.utils.dspy_utils import get_openrouter_llm

def llm_summarize(text: str, llm: Optional[object] = None) -> str:
    """Augment text by summarizing it using an LLM (DSPy/OpenRouter)."""
    if llm is None:
        llm = get_openrouter_llm()
    prompt = f"Summarize the following text for improved retrieval and semantic search.\n\nText:\n{text}\n\nSummary:"
    result = llm(prompt)
    if hasattr(result, 'text'):
        return result.text.strip()
    elif isinstance(result, str):
        return result.strip()
    return text

def llm_extract_metadata(text: str, llm: Optional[object] = None) -> Dict[str, Any]:
    """Extract structured metadata from text using an LLM."""
    if llm is None:
        llm = get_openrouter_llm()
    prompt = (
        f"Extract key metadata fields from the following text. "
        f"Return a JSON object with possible fields: title, author, date, tags, summary.\n\nText:\n{text}\n\nMetadata:"
    )
    result = llm(prompt)
    import json
    if hasattr(result, 'text'):
        try:
            return json.loads(result.text.strip())
        except Exception:
            return {"raw": result.text.strip()}
    elif isinstance(result, str):
        try:
            return json.loads(result.strip())
        except Exception:
            return {"raw": result.strip()}
    return {}

def llm_normalize_language(text: str, target_language: str = "en", llm: Optional[object] = None) -> str:
    """Normalize text to a target language using an LLM."""
    if llm is None:
        llm = get_openrouter_llm()
    prompt = f"Translate and normalize the following text to {target_language}.\n\nText:\n{text}\n\nNormalized ({target_language}):"
    result = llm(prompt)
    if hasattr(result, 'text'):
        return result.text.strip()
    elif isinstance(result, str):
        return result.strip()
    return text

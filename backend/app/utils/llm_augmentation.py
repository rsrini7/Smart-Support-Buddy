import dspy
import json
from typing import Optional, Dict, Any
from app.utils.dspy_utils import get_openrouter_llm

# Define DSPy Signatures
class SummarizeSignature(dspy.Signature):
    """Summarize the text for improved retrieval and semantic search."""
    text = dspy.InputField(desc="The text to summarize.")
    summary = dspy.OutputField(desc="A concise summary of the text.")

class ExtractMetadataSignature(dspy.Signature):
    """Extract key metadata fields from the text and return as a JSON object.
    Possible fields: title, author, date, tags, summary."""
    text = dspy.InputField(desc="The text to extract metadata from.")
    metadata_json = dspy.OutputField(desc="A JSON object containing extracted metadata (title, author, date, tags, summary).", prefix="Metadata JSON:")

class NormalizeLanguageSignature(dspy.Signature):
    """Translate and normalize the text to the target language."""
    text = dspy.InputField(desc="The text to normalize.")
    target_language = dspy.InputField(desc="The target language code (e.g., 'en', 'es').")
    normalized_text = dspy.OutputField(desc="The text normalized to the target language.")

# Refactored Functions using dspy.Predict
def llm_predict_with_signature(signature, input_kwargs, llm=None, max_tokens=None):
    """
    Generic utility to call a DSPy predictor with a given signature and input kwargs.
    """
    if llm is None:
        llm = get_openrouter_llm()
    with dspy.context(lm=llm):
        predictor = dspy.Predict(signature, max_tokens=max_tokens) if max_tokens else dspy.Predict(signature)
        return predictor(**input_kwargs)


def llm_summarize(text: str, llm: Optional[dspy.LM] = None) -> str:
    """Augment text by summarizing it using dspy.Predict."""
    result = llm_predict_with_signature(SummarizeSignature, {'text': text}, llm=llm, max_tokens=150)
    return result.summary


def llm_extract_metadata(text: str, llm: Optional[dspy.LM] = None) -> Dict[str, Any]:
    """Extract structured metadata from text using dspy.Predict."""
    result = llm_predict_with_signature(ExtractMetadataSignature, {'text': text}, llm=llm, max_tokens=200)
    try:
        metadata = json.loads(result.metadata_json.strip())
        if isinstance(metadata, dict):
            return metadata
        else:
            return {"raw": result.metadata_json.strip()}
    except json.JSONDecodeError:
        return {"raw": result.metadata_json.strip()}
    except Exception:
        return {"raw": result.metadata_json.strip()}


def llm_normalize_language(text: str, target_language: str = "en", llm: Optional[dspy.LM] = None) -> str:
    """Normalize text to a target language using dspy.Predict."""
    result = llm_predict_with_signature(
        NormalizeLanguageSignature,
        {'text': text, 'target_language': target_language},
        llm=llm,
        max_tokens=len(text) + 50
    )
    return result.normalized_text

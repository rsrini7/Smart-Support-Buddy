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
def llm_summarize(text: str, llm: Optional[dspy.LM] = None) -> str:
    """Augment text by summarizing it using dspy.Predict."""
    if llm is None:
        llm = get_openrouter_llm()
    with dspy.context(lm=llm):
        summarizer = dspy.Predict(SummarizeSignature, max_tokens=150) # Adjust max_tokens as needed
        result = summarizer(text=text)
        return result.summary

def llm_extract_metadata(text: str, llm: Optional[dspy.LM] = None) -> Dict[str, Any]:
    """Extract structured metadata from text using dspy.Predict."""
    if llm is None:
        llm = get_openrouter_llm()
    with dspy.context(lm=llm):
        extractor = dspy.Predict(ExtractMetadataSignature, max_tokens=200) # Adjust max_tokens as needed
        result = extractor(text=text)
        try:
            # Attempt to parse the JSON output
            metadata = json.loads(result.metadata_json.strip())
            if isinstance(metadata, dict):
                return metadata
            else:
                 # Handle cases where the LLM might not return a valid JSON object string
                return {"raw": result.metadata_json.strip()}
        except json.JSONDecodeError:
            # Return the raw output if JSON parsing fails
            return {"raw": result.metadata_json.strip()}
        except Exception:
             # Fallback for other potential errors
            return {"raw": result.metadata_json.strip()}

def llm_normalize_language(text: str, target_language: str = "en", llm: Optional[dspy.LM] = None) -> str:
    """Normalize text to a target language using dspy.Predict."""
    if llm is None:
        llm = get_openrouter_llm()
    with dspy.context(lm=llm):
        normalizer = dspy.Predict(NormalizeLanguageSignature, max_tokens=len(text) + 50) # Estimate max_tokens
        result = normalizer(text=text, target_language=target_language)
        return result.normalized_text

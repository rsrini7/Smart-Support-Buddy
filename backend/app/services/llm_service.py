import logging
import dspy
from app.core.config import settings
from app.utils import dspy_utils # Import dspy_utils
from app.utils.llm_augmentation import llm_predict_with_signature, SummarizeSignature

logger = logging.getLogger(__name__)

# Define DSPy Signature for Summarization
class SummarizeActionPoints(dspy.Signature):
    """Summarize the provided context from technical support search results into key action points."""
    context = dspy.InputField(desc="Concatenated text from top search results including titles, descriptions, root causes, solutions, and relevant metadata.")
    action_points = dspy.OutputField(desc="A concise summary or list of key action points based on the context.")

# Initialize the DSPy Predictor
try:
    lm = dspy_utils.get_openrouter_llm() # Get configured LM
    summarize_predictor = dspy.Predict(SummarizeActionPoints)
except Exception as e:
    logger.error(f"Failed to initialize DSPy LM or Predictor: {e}")
    # Handle initialization failure appropriately, maybe raise an error or use a fallback
    summarize_predictor = None
    lm = None


def generate_summary_from_results(results: list) -> str:
    """
    Generates a prompt from the top search results and calls the LLM.
    """
    if not results:
        return ""

    # Take top N results (configurable, file-backed)
    top_results = results[:settings.LLM_TOP_RESULTS]

    logger.info(f"Top results: {top_results}")

    # Construct prompt
    prompt_context = "Based on the following top search results, please provide key action points:\n\n"
    for i, result in enumerate(top_results):
        title = result.get('title', 'N/A')
        source_type = result.get('type', 'Unknown').replace('_', ' ').title()
        description = result.get('description', '')[:2000]
        similarity_score = result.get('similarity_score', None)
        root_cause = result.get('root_cause') or (result.get('msg_data', {}) or {}).get('root_cause')
        solution = result.get('solution') or (result.get('msg_data', {}) or {}).get('solution')

        prompt_context += f"Result {i+1} (Type: {source_type}):\n"
        prompt_context += f"Title: {title}\n"
        if similarity_score is not None:
            prompt_context += f"Similarity Score: {similarity_score:.2f}\n"
        prompt_context += f"Description: {description}\n"
        if root_cause:
            prompt_context += f"Root Cause: {root_cause}\n"
        if solution:
            prompt_context += f"Solution: {solution}\n"
        msg_data = result.get('msg_data')
        if msg_data:
            prompt_context += "MSG Data:\n"
            prompt_context += f"  Subject: {msg_data.get('subject', 'N/A')}\n"
            prompt_context += f"  Sender: {msg_data.get('sender', 'N/A')}\n"
            prompt_context += f"  Recipients: {msg_data.get('recipients', 'N/A')}\n"
            prompt_context += f"  Received Date: {msg_data.get('received_date', 'N/A')}\n"
            prompt_context += f"  Body: {msg_data.get('body', '')[:500]}\n"
        jira_data = result.get('jira_data')
        if jira_data:
            prompt_context += "Jira Ticket Data:\n"
            prompt_context += f"  Key: {jira_data.get('key', 'N/A')}\n"
            prompt_context += f"  Summary: {jira_data.get('summary', 'N/A')}\n"
            prompt_context += f"  Description: {jira_data.get('description', 'N/A')}\n"
            prompt_context += f"  Status: {jira_data.get('status', 'N/A')}\n"
            prompt_context += f"  Assignee: {jira_data.get('assignee', 'N/A')}\n"
            prompt_context += f"  Reporter: {jira_data.get('reporter', 'N/A')}\n"
            prompt_context += f"  Priority: {jira_data.get('priority', 'N/A')}\n"
            prompt_context += f"  Resolution: {jira_data.get('resolution', 'N/A')}\n"
            prompt_context += f"  Labels: {jira_data.get('labels', 'N/A')}\n"
            prompt_context += f"  Components: {jira_data.get('components', 'N/A')}\n"
            prompt_context += f"  Created: {jira_data.get('created', 'N/A')}\n"
            prompt_context += f"  Updated: {jira_data.get('updated', 'N/A')}\n"
        confluence_data = result.get('confluence_data')
        if confluence_data:
            prompt_context += "Confluence Data:\n"
            prompt_context += f"  Page ID: {confluence_data.get('page_id', 'N/A')}\n"
            prompt_context += f"  Title: {confluence_data.get('title', 'N/A')}\n"
            prompt_context += f"  URL: {confluence_data.get('url', 'N/A')}\n"
            prompt_context += f"  Space: {confluence_data.get('space', 'N/A')}\n"
            prompt_context += f"  Labels: {confluence_data.get('labels', 'N/A')}\n"
            prompt_context += f"  Creator: {confluence_data.get('creator', 'N/A')}\n"
            prompt_context += f"  Created: {confluence_data.get('created', 'N/A')}\n"
            prompt_context += f"  Updated: {confluence_data.get('updated', 'N/A')}\n"
            prompt_context += f"  Content: {confluence_data.get('content', 'N/A')[:500]}\n"
            prompt_context += f"  Similarity Score: {confluence_data.get('similarity_score', 'N/A')}\n"
        so_data = result.get('stackoverflow_data')
        if so_data:
            prompt_context += "Stack Overflow Q&A Data:\n"
            prompt_context += f"  Question ID: {so_data.get('question_id', 'N/A')}\n"
            prompt_context += f"  Question: {so_data.get('question_text', 'N/A')}\n"
            prompt_context += f"  Answer ID: {so_data.get('answer_id', 'N/A')}\n"
            prompt_context += f"  Answer: {so_data.get('answer_text', 'N/A')}\n"
            prompt_context += f"  Tags: {so_data.get('tags', 'N/A')}\n"
            prompt_context += f"  Author: {so_data.get('author', 'N/A')}\n"
            prompt_context += f"  Creation Date: {so_data.get('creation_date', 'N/A')}\n"
            prompt_context += f"  Score: {so_data.get('score', 'N/A')}\n"
            prompt_context += f"  Link: {so_data.get('link', 'N/A')}\n"
            prompt_context += f"  Content Hash: {so_data.get('content_hash', 'N/A')}\n"
            prompt_context += f"  Similarity Score: {so_data.get('similarity_score', 'N/A')}\n"

    # Call LLM using the generic utility
    result = llm_predict_with_signature(
        SummarizeSignature,
        {'text': prompt_context},
        max_tokens=350
    )
    return result.summary

# Example usage (for testing)
if __name__ == "__main__":
    # Mock results for testing
    mock_results = [
        {
            "type": "vector_issue",
            "title": "Login fails after password reset",
            "description": "User reports being unable to log in after successfully resetting their password. Error message 'Invalid credentials' displayed. Checked logs, password hash updated correctly. Suspect cache issue on client side.",
            "similarity_score": 0.95,
            "root_cause": "Cache issue on client side",
            "solution": "Clear cache and cookies"
        },
        {
            "type": "confluence",
            "title": "Troubleshooting Login Issues",
            "description": "Common login problems include incorrect username/password, locked accounts, and browser cache/cookies. Steps to resolve: 1. Verify credentials. 2. Try incognito mode. 3. Clear cache and cookies. 4. Contact support if issues persist.",
            "similarity_score": 0.88,
            "url": "https://confluence.example.com/display/KB/Troubleshooting+Login+Issues"
        },
        {
            "type": "stackoverflow",
            "title": "Flask login not working after password change",
            "description": "My Flask app uses Flask-Login. When a user changes their password, they can't log back in immediately. I'm updating the password hash in the database correctly. Is there a session issue?",
            "similarity_score": 0.85,
            "url": "https://stackoverflow.com/questions/12345/flask-login-not-working"
        }
    ]

    print("--- Generating Action --- ")
    # Ensure DSPy components are initialized before calling
    if summarize_predictor and lm:
        summary = generate_summary_from_results(mock_results)
        print("\n--- LLM Action --- ")
        print(summary)
    else:
        print("\n--- LLM Action --- ")
        print("Error: DSPy components not initialized, cannot run example.")
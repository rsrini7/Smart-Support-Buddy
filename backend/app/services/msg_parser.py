import extract_msg
import os
from typing import Dict, Any
import logging
import datetime
import re
import traceback


logger = logging.getLogger(__name__)

COLLECTION_NAME = "msg_files"

# --- LOGGING INSTRUMENTATION START ---
def log_ingest_start(file_path, extra_metadata):
    logger.info(f"[INGEST][START] MSG ingest called. File: {file_path}, Extra metadata keys: {list(extra_metadata.keys()) if extra_metadata else None}")

def log_ingest_success(ids):
    logger.info(f"[INGEST][SUCCESS] MSG file(s) successfully ingested. IDs: {ids}")

def log_ingest_failure(error):
    logger.error(f"[INGEST][FAILURE] MSG ingest failed: {error}")

def log_search_start(query_text, limit):
    logger.info(f"[SEARCH][START] MSG search called. Query: '{query_text}', Limit: {limit}")

def log_search_success(results_count):
    logger.info(f"[SEARCH][SUCCESS] MSG search returned {results_count} results.")

def log_search_failure(error):
    logger.error(f"[SEARCH][FAILURE] MSG search failed: {error}")
# --- LOGGING INSTRUMENTATION END ---

from app.utils.rag_utils import load_components, index_vector_data, create_bm25_index, create_retrievers, create_rag_pipeline
from app.services.embedding_service import get_embedding_model
from app.services.chroma_client import get_vector_db_client
from app.utils.llm_augmentation import llm_summarize
from app.utils.dspy_utils import get_openrouter_llm

_rag_pipeline = None
_corpus = None

def add_msg_file_to_vectordb(file_path: str, extra_metadata: dict = None, llm_augment=None, augment_metadata=True, normalize_language=True, target_language="en") -> str:
    log_ingest_start(file_path, extra_metadata)
    try:
        msg_data = parse_msg_file(file_path)
        if msg_data.get("status") == "error":
            raise ValueError(f"Failed to parse MSG file: {msg_data.get('error')}")
        subject = msg_data.get("subject", "")
        body = msg_data.get("body", "")
        sender = msg_data.get("sender", "")
        received_date = msg_data.get("received_date", None)
        recipients = msg_data.get("recipients", [])
        jira_info = extract_issue_details(msg_data)
        jira_id = jira_info.get("jira_id")
        jira_url = jira_info.get("jira_url")
        # Combine all text for embedding
        doc_text = f"Subject: {subject}\nBody: {body}\nSender: {sender}\nRecipients: {', '.join(recipients)}"
        if jira_id:
            doc_text += f"\nJira ID: {jira_id}"
        if jira_url:
            doc_text += f"\nJira URL: {jira_url}"
        doc_id = file_path
        metadata = {
            "msg_file_path": file_path,
            "msg_subject": subject,
            "msg_body": body,
            "msg_sender": sender,
            "msg_received_date": str(received_date) if received_date else None,
            "recipients": recipients,
            "jira_id": jira_id,
            "jira_url": jira_url,
        }
        if extra_metadata:
            metadata.update(extra_metadata)
        client = get_vector_db_client()
        embedder = get_embedding_model()
        ids = index_vector_data(
            client=client,
            embedder=embedder,
            documents=[doc_text],
            doc_ids=[doc_id],
            collection_name=COLLECTION_NAME,
            metadatas=[metadata],
            clear_existing=False,
            deduplicate=True,
            llm_augment=llm_augment or llm_summarize,
            augment_metadata=augment_metadata,
            normalize_language=normalize_language,
            target_language=target_language
        )
        log_ingest_success(ids)
        return ids[0] if ids else None
    except Exception as e:
        log_ingest_failure(e)
        return None

def _get_rag_pipeline():
    global _rag_pipeline, _corpus
    if _rag_pipeline is not None:
        return _rag_pipeline
    from app.core.config import settings
    client = get_vector_db_client()
    collection = client.get_collection(COLLECTION_NAME)
    results = collection.get()
    documents = results.get("documents", [])
    _corpus = documents
    embedder = get_embedding_model()
    reranker = None
    llm = get_openrouter_llm()
    bm25_processor = create_bm25_index(_corpus)
    vector_retriever, bm25_retriever = create_retrievers(collection, embedder, bm25_processor, _corpus)
    _rag_pipeline = create_rag_pipeline(vector_retriever, bm25_retriever, reranker, llm)
    return _rag_pipeline

def search_similar_msg_files(query_text: str, limit: int = 10):
    log_search_start(query_text, limit)
    try:
        rag_pipeline = _get_rag_pipeline()
        rag_result = rag_pipeline.forward(query_text)
        formatted = []
        for idx, context in enumerate(rag_result.context):
            formatted.append({
                "id": f"rag_{idx}",
                "title": context[:60],
                "content": context,
                "similarity_score": 1.0 if idx == 0 else 0.8,
                "metadata": {},
                "llm_answer": rag_result.answer if idx == 0 else None
            })
        log_search_success(len(formatted))
        return formatted
    except Exception as e:
        log_search_failure(e)
        return []

def parse_msg_file(file_path: str) -> Dict[str, Any]:
    logger.info(f"parse_msg_file called with file_path: {file_path}")
    try:
        if not os.path.exists(file_path):
            logger.error(f"File not found or invalid path: {file_path}")
            raise FileNotFoundError(f"MSG file not found at {file_path}")
        msg = extract_msg.Message(file_path)
        subject = msg.subject or "No Subject"
        sender = msg.sender or "Unknown Sender"
        body = msg.body or ""
        logger.info(f"Extracted subject: {subject}, sender: {sender}")
        recipients = []
        if msg.to is not None:
            if isinstance(msg.to, list):
                recipients.extend(msg.to)
            else:
                recipients.append(msg.to)
        received_date = None
        if msg.date is not None:
            received_date = msg.date
        elif getattr(msg, 'sent_date', None) is not None:
            received_date = msg.sent_date
        elif getattr(msg, 'delivery_time', None) is not None:
            received_date = msg.delivery_time
        else:
            from datetime import datetime as dt
            received_date = dt.now()
            logger.debug("[msg_parser] No date info found, using current datetime as received_date fallback")
        attachments = []
        # attachment_dir = os.path.join(os.path.dirname(file_path), "attachments", os.path.basename(file_path).split(".")[0])
        # os.makedirs(attachment_dir, exist_ok=True)
        # for attachment in msg.attachments:
        #     logger.info(f"Processing attachment: {getattr(attachment, 'longFilename', None)}")
        #     if attachment.longFilename:
        #         attachment_path = os.path.join(attachment_dir, attachment.longFilename)
        #         with open(attachment_path, "wb") as f:
        #             f.write(attachment.data)
        #         attachments.append(attachment_path)
        headers = {}
        if hasattr(msg, "header") and msg.header:
            if isinstance(msg.header, str):
                header_lines = msg.header.split("\n")
                for line in header_lines:
                    if ": " in line:
                        key, value = line.split(": ", 1)
                        headers[key.strip()] = value.strip()
            else:
                try:
                    headers["raw_header"] = str(msg.header)
                except Exception as e:
                    headers["header_error"] = f"Could not convert header to string: {e}"
        result = {
            "file_path": file_path,
            "subject": subject,
            "sender": sender,
            "recipients": recipients,
            "body": body,
            "received_date": received_date,
            # 'attachments': attachments,  # Remove attachments from result
            "headers": headers
        }
        extracted_details = extract_issue_details(result)
        result.update(extracted_details)
        def make_json_safe(obj):
            if isinstance(obj, (str, int, float, bool)) or obj is None:
                return obj
            elif isinstance(obj, dict):
                return {str(k): make_json_safe(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_json_safe(v) for v in obj]
            elif isinstance(obj, tuple):
                return tuple(make_json_safe(v) for v in obj)
            elif isinstance(obj, (datetime.datetime, datetime.date)):
                return obj.isoformat()
            elif isinstance(obj, str) and obj.count('-') >= 2 and 'T' in obj:
                return obj
            else:
                return f"<non-serializable: {type(obj).__name__}>"
        result = make_json_safe(result)
    except FileNotFoundError as fnf:
        logger.error(f"Error inside parse_msg_file for file_path {file_path}: {fnf}")
        logger.error(traceback.format_exc())
        raise
    except Exception as e:
        logger.error(f"Error inside parse_msg_file for file_path {file_path}: {e}")
        logger.error(traceback.format_exc())
        return {
            "file_path": file_path,
            "status": "error",
            "error": str(e) or "Unknown backend error",
            "error_type": type(e).__name__ if e else "UnknownError",
        }
    finally:
        if 'msg' in locals():
            try:
                msg.close()
            except Exception as close_err:
                logger.warning(f"Error closing MSG file: {close_err}")
    return result

def extract_issue_details(msg_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract RCA details from MSG data, including Jira ID, root cause, and solution.
    """
    body = msg_data.get("body", "") or ""
    subject = msg_data.get("subject", "") or ""
    combined_text = f"{subject}\n{body}"
    
    # Initialize result
    issue_details = {
        "title": subject,
        "description": body,
        "jira_id": None,
        "jira_url": None,
    }

    # Extract Jira ID and URL
    jira_pattern = r"\b[A-Z][A-Z0-9]+-\d+\b"
    jira_url_pattern = r"https?://[^\s]+/(?:browse|projects/.+/issues)/([A-Z][A-Z0-9]+-\d+)"

    # First try to find Jira URL
    url_match = re.search(jira_url_pattern, combined_text)
    if url_match:
        issue_details["jira_url"] = url_match.group(0)
        issue_details["jira_id"] = url_match.group(1)
    else:
        # If no URL found, look for Jira ID directly
        id_match = re.search(jira_pattern, combined_text)
        if id_match:
            issue_details["jira_id"] = id_match.group(0)

    return issue_details

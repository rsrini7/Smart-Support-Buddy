import extract_msg
import os
from typing import Dict, Any
import logging
import datetime

logger = logging.getLogger(__name__)


def parse_msg_file(file_path: str) -> Dict[str, Any]:
    """
    logger = logging.getLogger(__name__)
    logger.info(f"parse_msg_file called with file_path: {file_path}")
    try:
    Parse an Outlook MSG file and extract relevant information.
    
    Args:
        file_path: Path to the MSG file
        
    Returns:
        Dictionary containing extracted information from the MSG file
    """
    logger = logging.getLogger(__name__)
    logger.info(f"parse_msg_file called with file_path: {file_path}")

    try:
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"File not found or invalid path: {file_path}")
            raise FileNotFoundError(f"MSG file not found at {file_path}")
            
        # Open the MSG file
        msg = extract_msg.Message(file_path)
        
        # Extract basic information
        subject = msg.subject or "No Subject"
        sender = msg.sender or "Unknown Sender"
        body = msg.body or ""
        
        # Parse recipients
        recipients = []
        if msg.to is not None:
            if isinstance(msg.to, list):
                recipients.extend(msg.to)
            else:
                recipients.append(msg.to)
                
        # Parse received date
        received_date = None
        if msg.date is not None:
            received_date = msg.date
        elif getattr(msg, 'sent_date', None) is not None:
            received_date = msg.sent_date
        elif getattr(msg, 'delivery_time', None) is not None:
            received_date = msg.delivery_time
        else:
            # Fallback: use current datetime if no date info found
            from datetime import datetime as dt
            received_date = dt.now()
            logger.debug("[msg_parser] No date info found, using current datetime as received_date fallback")
            
        # Extract attachments
        attachments = []
        attachment_dir = os.path.join(os.path.dirname(file_path), "attachments", os.path.basename(file_path).split(".")[0])
        os.makedirs(attachment_dir, exist_ok=True)
        
        for attachment in msg.attachments:
            if attachment.longFilename:
                attachment_path = os.path.join(attachment_dir, attachment.longFilename)
                with open(attachment_path, "wb") as f:
                    f.write(attachment.data)
                attachments.append(attachment_path)
        
        # Extract headers
        headers = {}
        # Restore original logic: attempt string split, fallback to str(msg.header), but never attempt to iterate or serialize objects
        if hasattr(msg, "header") and msg.header:
            if isinstance(msg.header, str):
                header_lines = msg.header.split("\n")
                for line in header_lines:
                    if ": " in line:
                        key, value = line.split(": ", 1)
                        headers[key.strip()] = value.strip()
            else:
                # Fallback: just store the string representation, never the object itself
                try:
                    headers["raw_header"] = str(msg.header)
                except Exception as e:
                    headers["header_error"] = f"Could not convert header to string: {e}"
        
        # Create result dictionary
        result = {
            "file_path": file_path,
            "subject": subject,
            "sender": sender,
            "recipients": recipients,
            "body": body,
            "received_date": received_date,
            "attachments": attachments,
            "headers": headers
        }
        
        # Extract additional issue details (Jira ID, root cause, solution)
        extracted_details = extract_issue_details(result)
        result.update(extracted_details)

        def make_json_safe(obj):
            """Recursively convert any object to a JSON-safe primitive."""
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
            # PATCH: if someone already called isoformat() on a date and it's a string, just return it
            elif isinstance(obj, str) and obj.count('-') >= 2 and 'T' in obj:
                return obj
            else:
                # Fallback: just show the type
                return f"<non-serializable: {type(obj).__name__}>"

        # FINAL PATCH: sanitize all output for JSON serialization
        result = make_json_safe(result)

    except Exception as e:
        logger.error(f"Error inside parse_msg_file for file_path {file_path}: {e}")
        # Always return a JSON-safe error result to the caller, never raise
        return {
            "file_path": file_path,
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
        }
    finally:
        # Close the MSG file
        if 'msg' in locals():
            try:
                msg.close()
            except Exception as close_err:
                logger.warning(f"Error closing MSG file: {close_err}")
    return result

import re

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

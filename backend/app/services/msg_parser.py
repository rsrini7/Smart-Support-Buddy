import extract_msg
import os
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def parse_msg_file(file_path: str) -> Dict[str, Any]:
    """
    Parse an Outlook MSG file and extract relevant information.
    
    Args:
        file_path: Path to the MSG file
        
    Returns:
        Dictionary containing extracted information from the MSG file
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
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
        if hasattr(msg, "header") and msg.header:
            # Parse headers into a dictionary
            # Check if header is a string before attempting to split
            if isinstance(msg.header, str):
                header_lines = msg.header.split("\n")
                for line in header_lines:
                    if ": " in line:
                        key, value = line.split(": ", 1)
                        headers[key.strip()] = value.strip()
            else:
                # If header is not a string, try to convert it to string or extract header data another way
                logger.warning(f"MSG header is not a string type: {type(msg.header)}")
                # Add header as is if it's a dictionary or try to convert to string
                if isinstance(msg.header, dict):
                    headers = msg.header
                else:
                    try:
                        # Try to convert to string if possible
                        header_str = str(msg.header)
                        headers["raw_header"] = header_str
                    except:
                        # If conversion fails, just log and continue
                        logger.warning("Could not process header data")
        
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

        # Log the final parsed result
        try:
            import json as _json
            logger.debug("Parsed MSG file result: %s", _json.dumps(result, indent=2, default=str))
        except Exception:
            logger.debug("Parsed MSG file result (non-JSON): %s", str(result))

        # Close the MSG file
        msg.close()
        
        return result
    
    except Exception as e:
        logger.error(f"Error parsing MSG file: {str(e)}")
        raise

import re

def extract_issue_details(msg_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract production issue details from MSG data, including Jira ID, root cause, and solution.
    
    Args:
        msg_data: Dictionary containing MSG file data
        
    Returns:
        Dictionary with extracted issue details
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
        "root_cause": None,
        "solution": None,
    }
    
    # --- Extract Jira ID ---
    # Typical Jira ID pattern: ABC-1234
    jira_pattern = r"\b[A-Z][A-Z0-9]+-\d+\b"
    jira_matches = re.findall(jira_pattern, combined_text)
    if jira_matches:
        issue_details["jira_id"] = jira_matches[0]

        # Search for Jira URL in the text
        jira_url_pattern = r"https?://[^\s]+/browse/[A-Z][A-Z0-9]+-\d+"
        jira_url_match = re.search(jira_url_pattern, combined_text)
        if jira_url_match:
            issue_details["jira_url"] = jira_url_match.group(0)
        else:
            issue_details["jira_url"] = None
    
    # --- Extract root cause and solution sections ---
    lines = combined_text.splitlines()
    capture_root_cause = False
    capture_solution = False
    root_cause_lines = []
    solution_lines = []
    
    for line in lines:
        lower_line = line.lower()
        # Start capturing root cause
        if any(term in lower_line for term in ["root cause", "reason", "rca", "identified issue", "why this happened", "issue caused by"]):
            capture_root_cause = True
            capture_solution = False
            continue
        # Start capturing solution
        if any(term in lower_line for term in ["solution", "resolution", "resolved", "workaround", "fix"]):
            capture_solution = True
            capture_root_cause = False
            continue
        # Stop capturing on empty line or new section header
        if line.strip() == "" or any(h in lower_line for h in ["steps", "impact", "next steps", "action items", "summary"]):
            capture_root_cause = False
            capture_solution = False
            continue
        # Append lines
        if capture_root_cause:
            root_cause_lines.append(line)
        if capture_solution:
            solution_lines.append(line)
    
    if root_cause_lines:
        issue_details["root_cause"] = "\n".join(root_cause_lines).strip()
    if solution_lines:
        issue_details["solution"] = "\n".join(solution_lines).strip()
    
    return issue_details
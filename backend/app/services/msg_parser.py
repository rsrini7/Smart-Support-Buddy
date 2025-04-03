import extract_msg
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
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
        
        # Close the MSG file
        msg.close()
        
        return result
    
    except Exception as e:
        logger.error(f"Error parsing MSG file: {str(e)}")
        raise

def extract_issue_details(msg_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract production issue details from MSG data.
    This function can be enhanced with NLP to better extract structured information.
    
    Args:
        msg_data: Dictionary containing MSG file data
        
    Returns:
        Dictionary with extracted issue details
    """
    # Basic extraction - this could be enhanced with NLP/LLM processing
    body = msg_data.get("body", "")
    subject = msg_data.get("subject", "")
    
    # Simple heuristic to extract potential issue details
    # In a real implementation, this would use more sophisticated NLP
    issue_details = {
        "title": subject,
        "description": body,
        "potential_root_cause": None,
        "potential_solution": None,
    }
    
    # Look for sections that might indicate root cause or solution
    # This is a very basic approach and would be improved with NLP
    lower_body = body.lower()
    
    # Look for root cause indicators
    root_cause_indicators = ["root cause", "cause", "reason", "why this happened", "issue caused by"]
    for indicator in root_cause_indicators:
        if indicator in lower_body:
            # Find the paragraph containing this indicator
            paragraphs = body.split("\n\n")
            for para in paragraphs:
                if indicator in para.lower():
                    issue_details["potential_root_cause"] = para.strip()
                    break
    
    # Look for solution indicators
    solution_indicators = ["solution", "resolution", "fixed by", "resolved by", "workaround"]
    for indicator in solution_indicators:
        if indicator in lower_body:
            # Find the paragraph containing this indicator
            paragraphs = body.split("\n\n")
            for para in paragraphs:
                if indicator in para.lower():
                    issue_details["potential_solution"] = para.strip()
                    break
    
    return issue_details
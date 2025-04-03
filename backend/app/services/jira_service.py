from jira import JIRA
from typing import Dict, Any, List, Optional, Union
import logging
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Jira client
def get_jira_client():
    """
    Get a Jira client instance using credentials from settings.
    
    Returns:
        JIRA client instance or None if credentials are not configured
    """
    try:
        if not all([settings.JIRA_URL, settings.JIRA_USERNAME, settings.JIRA_API_TOKEN]):
            logger.warning("Jira credentials not fully configured")
            return None
            
        jira = JIRA(
            server=settings.JIRA_URL,
            basic_auth=(settings.JIRA_USERNAME, settings.JIRA_API_TOKEN)
        )
        return jira
    except Exception as e:
        logger.error(f"Error initializing Jira client: {str(e)}")
        return None

def get_jira_ticket(ticket_id: str) -> Optional[Dict[str, Any]]:
    """
    Get information about a Jira ticket.
    
    Args:
        ticket_id: Jira ticket ID or key
        
    Returns:
        Dictionary containing Jira ticket information or None if not found
    """
    try:
        jira = get_jira_client()
        if not jira:
            logger.warning("Jira client not available")
            return None
            
        issue = jira.issue(ticket_id)
        if not issue:
            return None
            
        # Extract fields from the issue
        fields = issue.fields
        
        # Parse components
        components = []
        if hasattr(fields, 'components'):
            components = [c.name for c in fields.components]
            
        # Parse labels
        labels = []
        if hasattr(fields, 'labels'):
            labels = fields.labels
            
        # Parse custom fields
        custom_fields = {}
        for field_name in dir(fields):
            if field_name.startswith('customfield_'):
                value = getattr(fields, field_name)
                if value is not None:
                    custom_fields[field_name] = str(value)
        
        # Create result dictionary
        result = {
            "id": issue.id,
            "key": issue.key,
            "summary": fields.summary,
            "description": fields.description,
            "status": fields.status.name,
            "created": datetime.strptime(fields.created, '%Y-%m-%dT%H:%M:%S.%f%z'),
            "updated": datetime.strptime(fields.updated, '%Y-%m-%dT%H:%M:%S.%f%z'),
            "assignee": fields.assignee.displayName if fields.assignee else None,
            "reporter": fields.reporter.displayName if fields.reporter else None,
            "priority": fields.priority.name if fields.priority else None,
            "resolution": fields.resolution.name if fields.resolution else None,
            "components": components,
            "labels": labels,
            "custom_fields": custom_fields
        }
        
        return result
    
    except Exception as e:
        logger.error(f"Error getting Jira ticket {ticket_id}: {str(e)}")
        return None

def link_msg_to_jira(msg_data: Dict[str, Any], jira_data: Dict[str, Any]) -> bool:
    """
    Link an MSG file to a Jira ticket by adding a comment with the MSG information.
    
    Args:
        msg_data: Dictionary containing MSG file data
        jira_data: Dictionary containing Jira ticket data
        
    Returns:
        True if successful, False otherwise
    """
    try:
        jira = get_jira_client()
        if not jira:
            logger.warning("Jira client not available")
            return False
            
        ticket_key = jira_data.get("key")
        if not ticket_key:
            logger.error("No ticket key provided")
            return False
            
        # Create a comment with MSG information
        comment = f"""Production issue email linked:
        
        Subject: {msg_data.get('subject', 'No Subject')}
        From: {msg_data.get('sender', 'Unknown')}
        Date: {msg_data.get('received_date', 'Unknown')}
        
        Email Body:
        {msg_data.get('body', 'No content')}"""  
        
        # Add the comment to the issue
        jira.add_comment(ticket_key, comment)
        
        # Optionally, add attachments from the MSG file
        attachments = msg_data.get("attachments", [])
        for attachment_path in attachments:
            jira.add_attachment(issue=ticket_key, attachment=attachment_path)
            
        return True
    
    except Exception as e:
        logger.error(f"Error linking MSG to Jira ticket: {str(e)}")
        return False

def extract_root_cause_solution(jira_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract root cause and solution information from Jira ticket data.
    
    Args:
        jira_data: Dictionary containing Jira ticket data
        
    Returns:
        Dictionary with extracted root cause and solution
    """
    result = {
        "root_cause": None,
        "solution": None
    }
    
    # Check if Jira data is available
    if not jira_data:
        return result
        
    # Extract from description
    description = jira_data.get("description", "")
    if description:
        # Look for root cause section
        if "root cause" in description.lower():
            lines = description.split("\n")
            capture_root_cause = False
            root_cause_lines = []
            
            for line in lines:
                if "root cause" in line.lower():
                    capture_root_cause = True
                    continue
                elif capture_root_cause and (line.strip() == "" or any(header in line.lower() for header in ["solution", "resolution", "steps"])):
                    capture_root_cause = False
                elif capture_root_cause:
                    root_cause_lines.append(line)
                    
            if root_cause_lines:
                result["root_cause"] = "\n".join(root_cause_lines).strip()
        
        # Look for solution section
        if any(term in description.lower() for term in ["solution", "resolution", "workaround"]):
            lines = description.split("\n")
            capture_solution = False
            solution_lines = []
            
            for line in lines:
                if any(term in line.lower() for term in ["solution", "resolution", "workaround"]):
                    capture_solution = True
                    continue
                elif capture_solution and (line.strip() == "" or any(header in line.lower() for header in ["steps to reproduce", "impact"])):
                    capture_solution = False
                elif capture_solution:
                    solution_lines.append(line)
                    
            if solution_lines:
                result["solution"] = "\n".join(solution_lines).strip()
    
    # Check custom fields for root cause or solution
    custom_fields = jira_data.get("custom_fields", {})
    for field_name, value in custom_fields.items():
        if "root" in field_name.lower() and "cause" in field_name.lower() and not result["root_cause"]:
            result["root_cause"] = value
        elif any(term in field_name.lower() for term in ["solution", "resolution", "fix"]) and not result["solution"]:
            result["solution"] = value
    
    return result
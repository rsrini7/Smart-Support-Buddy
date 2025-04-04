from jira import JIRA
from typing import Dict, Any, List, Optional, Union
import logging
from datetime import datetime

from app.core.config import settings
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Initialize Jira client
def get_jira_client():
    """
    Get a Jira client instance using credentials from settings.
    
    Returns:
        JIRA client instance
    
    Raises:
        HTTPException: If Jira credentials are missing or invalid
    """
    logger.info("Initializing Jira client with provided configuration")
    logger.info(f"Attempting to connect with username: {settings.JIRA_USERNAME}")
    logger.info(f"Jira URL configured as: {settings.JIRA_URL}")
    logger.debug(f"API token present: {'Yes' if settings.JIRA_API_TOKEN else 'No'}")
    logger.debug(f"API token length: {len(settings.JIRA_API_TOKEN) if settings.JIRA_API_TOKEN else 0}")
    
    # Check if Jira configuration is valid
    if not settings.has_valid_jira_config:
        error_msg = "Invalid Jira configuration. Please check your environment variables."
        logger.error(error_msg)
        raise HTTPException(
            status_code=401,
            detail=error_msg
        )
            
    try:
        # Normalize and validate Jira URL
        jira_url = settings.JIRA_URL.strip() if settings.JIRA_URL else ""
        if not jira_url.startswith(('http://', 'https://')):
            logger.info(f"Adding HTTPS protocol to Jira URL: {jira_url}")
            jira_url = f'https://{jira_url}'
        
        # Force HTTPS for Atlassian Cloud instances
        if 'atlassian.net' in jira_url:
            logger.info("Detected Atlassian Cloud instance, forcing HTTPS")
            jira_url = jira_url.replace('http://', 'https://')

        logger.info(f"Attempting to connect to Jira at: {jira_url}")
        logger.debug(f"Connection details - Username: {settings.JIRA_USERNAME}, Token Length: {len(settings.JIRA_API_TOKEN) if settings.JIRA_API_TOKEN else 0}")

        # Initialize Jira client with proper authentication and options
        # For local Jira instance, always use password authentication
        is_local = 'localhost' in jira_url or '127.0.0.1' in jira_url or 'jira:9090' in jira_url
        
        # For local instance, ensure we're using password authentication
        if is_local:
            if not settings.JIRA_PASSWORD:
                logger.error("Password is required for local Jira instance")
                raise HTTPException(
                    status_code=401,
                    detail="Password is required for local Jira instance"
                )
            auth_tuple = (settings.JIRA_USERNAME.strip(), settings.JIRA_PASSWORD.strip())
        else:
            if not settings.JIRA_API_TOKEN:
                logger.error("API token is required for cloud Jira instance")
                raise HTTPException(
                    status_code=401,
                    detail="API token is required for cloud Jira instance"
                )
            auth_tuple = (settings.JIRA_USERNAME.strip(), settings.JIRA_API_TOKEN.strip())
        
        logger.info(f"Using {'password' if is_local else 'API token'} authentication for {'local' if is_local else 'cloud'} instance")
        
        # Configure client options based on environment
        options = {
            'server': jira_url,
            'verify': not is_local,  # Skip SSL verification for local instance
        }
        
        jira = JIRA(
            options=options,
            basic_auth=auth_tuple,
            validate=True,
            max_retries=3
        )

        # Verify connection and permissions
        try:
            user = jira.myself()
            logger.info(f"Successfully authenticated as {user['displayName']} with Jira instance")
            return jira
        except Exception as auth_error:
            error_msg = str(auth_error).lower()
            if 'unauthorized' in error_msg or 'authentication' in error_msg:
                logger.error(f"Authentication failed: Invalid credentials for user {settings.JIRA_USERNAME}")
                raise HTTPException(
                    status_code=401,
                    detail="Invalid credentials. Please verify your Jira username and API token."
                )
            elif 'forbidden' in error_msg:
                logger.error(f"Authentication failed: Insufficient permissions for user {settings.JIRA_USERNAME}")
                raise HTTPException(
                    status_code=403,
                    detail="Insufficient permissions. Please check your Jira account permissions."
                )
            else:
                logger.error(f"Authentication failed with unexpected error: {error_msg}")
                raise HTTPException(
                    status_code=401,
                    detail=f"Authentication failed: {str(auth_error)}"
                )

    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error initializing Jira client: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=500,
            detail="Failed to connect to Jira. Please check your configuration and network connection."
        )

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
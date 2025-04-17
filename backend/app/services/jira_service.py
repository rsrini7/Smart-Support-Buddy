from jira import JIRA
from typing import Dict, Any, Optional
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
        
        # Replace 'jira' with 'localhost' for local development
        if jira_url == 'jira:9090' or jira_url == 'http://jira:9090' or jira_url == 'https://jira:9090':
            logger.info("Detected local Jira instance with 'jira' hostname, replacing with 'localhost'")
            jira_url = 'http://localhost:9090'
        
        # For local development (localhost), always use HTTP
        if 'localhost' in jira_url or '127.0.0.1' in jira_url:
            if jira_url.startswith('https://'):
                jira_url = jira_url.replace('https://', 'http://')
            elif not jira_url.startswith('http://'):
                jira_url = f'http://{jira_url}'
            logger.info(f"Using HTTP for local Jira instance: {jira_url}")
        else:
            # Add HTTPS protocol for non-local URLs if missing
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
                    detail="Password is required for local Jira instance. Please check your .env file."
                )
            if not settings.JIRA_USERNAME:
                logger.error("Username is required for local Jira instance")
                raise HTTPException(
                    status_code=401,
                    detail="Username is required for local Jira instance. Please check your .env file."
                )
            auth_tuple = (settings.JIRA_USERNAME.strip(), settings.JIRA_PASSWORD.strip())
            logger.info(f"Using basic authentication for local instance with username: {settings.JIRA_USERNAME}")
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
            'timeout': 10  # Add timeout to prevent hanging
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
            "created": datetime.strptime(fields.created, '%Y-%m-%dT%H:%M:%S.%f%z').isoformat(),
            "updated": datetime.strptime(fields.updated, '%Y-%m-%dT%H:%M:%S.%f%z').isoformat(),
            "assignee": fields.assignee.displayName if fields.assignee else None,
            "reporter": fields.reporter.displayName if fields.reporter else None,
            "priority": fields.priority.name if fields.priority else None,
            "resolution": fields.resolution.name if fields.resolution else None,
            "components": components,
            "labels": labels,
            "custom_fields": custom_fields
        }

        # Fetch comments
        comments_data = []
        try:
            comments = issue.fields.comment.comments
            for comment in comments:
                comments_data.append({
                    "author": comment.author.displayName if comment.author else "Unknown",
                    "created": comment.created,
                    "body": comment.body
                })
        except Exception as e:
            logger.warning(f"Failed to fetch comments for Jira ticket {ticket_id}: {e}")

        result["comments"] = comments_data

        return result
    
    except Exception as e:
        logger.error(f"Error getting Jira ticket {ticket_id}: {str(e)}")
        return None

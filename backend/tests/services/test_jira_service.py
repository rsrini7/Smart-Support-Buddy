import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from fastapi import HTTPException

from app.services.jira_service import get_jira_client, get_jira_ticket
from app.core.config import settings


class TestJiraService:
    
    @patch('app.services.jira_service.JIRA')
    def test_get_jira_client_success(self, mock_jira):
        # Setup mock
        mock_jira_instance = MagicMock()
        mock_jira_instance.myself.return_value = {'displayName': 'Test User'}
        mock_jira.return_value = mock_jira_instance
        
        # Mock settings
        with patch('app.services.jira_service.settings') as mock_settings:
            mock_settings.JIRA_URL = "https://jira.example.com"
            mock_settings.JIRA_USERNAME = "test_user"
            mock_settings.JIRA_API_TOKEN = "test_token"
            mock_settings.has_valid_jira_config = True
            
            # Call the function
            result = get_jira_client()
            
            # Assertions
            assert result == mock_jira_instance
            mock_jira.assert_called_once()
            mock_jira_instance.myself.assert_called_once()
    
    @patch('app.services.jira_service.JIRA')
    def test_get_jira_client_invalid_config(self, mock_jira):
        # Mock settings with invalid config
        with patch('app.services.jira_service.settings') as mock_settings:
            mock_settings.has_valid_jira_config = False
            
            # Call the function and expect exception
            with pytest.raises(HTTPException) as excinfo:
                get_jira_client()
            
            # Assertions
            assert excinfo.value.status_code == 401
            assert "Invalid Jira configuration" in excinfo.value.detail
            mock_jira.assert_not_called()
    
    @patch('app.services.jira_service.JIRA')
    def test_get_jira_client_auth_error(self, mock_jira):
        # Setup mock to raise authentication error
        mock_jira_instance = MagicMock()
        mock_jira_instance.myself.side_effect = Exception("Unauthorized")
        mock_jira.return_value = mock_jira_instance
        
        # Mock settings
        with patch('app.services.jira_service.settings') as mock_settings:
            mock_settings.JIRA_URL = "https://jira.example.com"
            mock_settings.JIRA_USERNAME = "test_user"
            mock_settings.JIRA_API_TOKEN = "test_token"
            mock_settings.has_valid_jira_config = True
            
            # Call the function and expect exception
            with pytest.raises(HTTPException) as excinfo:
                get_jira_client()
            
            # Assertions
            assert excinfo.value.status_code == 401
            assert "Invalid credentials" in excinfo.value.detail
    
    @patch('app.services.jira_service.get_jira_client')
    def test_get_jira_ticket_success(self, mock_get_client):
        # Setup mock issue
        mock_issue = MagicMock()
        mock_issue.id = "12345"
        mock_issue.key = "PROJ-123"
        
        # Setup mock fields
        mock_fields = MagicMock()
        mock_fields.summary = "Test Issue"
        mock_fields.description = "Test Description"
        mock_fields.status.name = "Open"
        mock_fields.created = "2023-01-01T12:00:00.000+0000"
        mock_fields.updated = "2023-01-02T12:00:00.000+0000"
        mock_fields.assignee.displayName = "Assignee User"
        mock_fields.reporter.displayName = "Reporter User"
        mock_fields.priority.name = "High"
        mock_fields.resolution.name = "Fixed"
        
        # Setup components and labels
        mock_component = MagicMock()
        mock_component.name = "Component1"
        mock_fields.components = [mock_component]
        mock_fields.labels = ["label1", "label2"]
        
        # Setup comments
        mock_comment = MagicMock()
        mock_comment.author.displayName = "Comment Author"
        mock_comment.created = "2023-01-03T12:00:00.000+0000"
        mock_comment.body = "Test comment"
        mock_fields.comment.comments = [mock_comment]
        
        # Attach fields to issue
        mock_issue.fields = mock_fields
        
        # Setup mock client
        mock_client = MagicMock()
        mock_client.issue.return_value = mock_issue
        mock_get_client.return_value = mock_client
        
        # Call the function
        result = get_jira_ticket("PROJ-123")
        
        # Assertions
        assert result is not None
        assert result["id"] == "12345"
        assert result["key"] == "PROJ-123"
        assert result["summary"] == "Test Issue"
        assert result["components"] == ["Component1"]
        assert result["labels"] == ["label1", "label2"]
        assert len(result["comments"]) == 1
        assert result["comments"][0]["author"] == "Comment Author"
    
    @patch('app.services.jira_service.get_jira_client')
    def test_get_jira_ticket_not_found(self, mock_get_client):
        # Setup mock client to return None for issue
        mock_client = MagicMock()
        mock_client.issue.return_value = None
        mock_get_client.return_value = mock_client
        
        # Call the function
        result = get_jira_ticket("NONEXISTENT-123")
        
        # Assertions
        assert result is None
        mock_client.issue.assert_called_once_with("NONEXISTENT-123")
    
    @patch('app.services.jira_service.get_jira_client')
    def test_get_jira_ticket_client_error(self, mock_get_client):
        # Setup mock client to raise exception
        mock_get_client.side_effect = Exception("Connection error")
        
        # Call the function
        result = get_jira_ticket("PROJ-123")
        
        # Assertions
        assert result is None
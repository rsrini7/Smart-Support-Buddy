import pytest
from unittest.mock import patch, MagicMock, mock_open
import os
from datetime import datetime

from app.services.msg_parser import parse_msg_file, extract_issue_details


class TestMsgParser:
    
    @pytest.fixture
    def mock_msg(self):
        mock = MagicMock()
        mock.subject = "Test Subject"
        mock.sender = "test@example.com"
        mock.body = "Test body content"
        mock.to = ["recipient1@example.com", "recipient2@example.com"]
        mock.date = datetime(2023, 1, 1, 12, 0, 0)
        mock.header = "From: test@example.com\nTo: recipient@example.com"
        mock.attachments = []
        return mock

    @patch('app.services.msg_parser.extract_msg.Message')
    @patch('app.services.msg_parser.os.path.exists')
    @patch('app.services.msg_parser.os.makedirs')
    def test_parse_msg_file_success(self, mock_makedirs, mock_exists, mock_message_class, mock_msg):
        # Setup
        mock_exists.return_value = True
        mock_message_class.return_value = mock_msg
        file_path = "/path/to/test.msg"

        # Execute
        result = parse_msg_file(file_path)

        # Assert
        assert result["subject"] == "Test Subject"
        assert result["sender"] == "test@example.com"
        assert result["body"] == "Test body content"
        assert result["recipients"] == ["recipient1@example.com", "recipient2@example.com"]
        assert result["received_date"] == "2023-01-01T12:00:00"
        assert isinstance(result["headers"], dict)
        assert result["attachments"] == []
        
        mock_exists.assert_called_once_with(file_path)
        mock_message_class.assert_called_once_with(file_path)
        mock_makedirs.assert_called_once()

    @patch('app.services.msg_parser.os.path.exists')
    def test_parse_msg_file_not_found(self, mock_exists):
        # Setup
        mock_exists.return_value = False
        file_path = "/path/to/nonexistent.msg"

        # Execute and Assert
        with pytest.raises(FileNotFoundError):
            parse_msg_file(file_path)

    @patch('app.services.msg_parser.extract_msg.Message')
    @patch('app.services.msg_parser.os.path.exists')
    @patch('app.services.msg_parser.os.makedirs')
    def test_parse_msg_file_with_attachments(self, mock_makedirs, mock_exists, mock_message_class):
        # Setup
        mock_msg = MagicMock()
        mock_msg.subject = "Test Subject"
        mock_msg.sender = "test@example.com"
        mock_msg.body = "Test body"
        mock_msg.to = "recipient@example.com"
        mock_msg.date = datetime.now()
        
        # Create mock attachment
        mock_attachment = MagicMock()
        mock_attachment.longFilename = "test.txt"
        mock_attachment.data = b"test content"
        mock_msg.attachments = [mock_attachment]
        
        mock_exists.return_value = True
        mock_message_class.return_value = mock_msg
        
        # Execute
        with patch('builtins.open', mock_open()) as mock_file:
            result = parse_msg_file("/path/to/test.msg")

        # Assert
        assert len(result["attachments"]) == 1
        assert "test.txt" in result["attachments"][0]
        mock_file.assert_called_once()

    def test_extract_issue_details_with_jira_id(self):
        # Setup
        msg_data = {
            "subject": "Issue with service PROJ-123",
            "body": "There is a problem with the service.\nJira ticket: PROJ-123",
            "title": "Issue with service PROJ-123",
            "description": "There is a problem with the service.\nJira ticket: PROJ-123",
            "jira_id": None,
            "jira_url": None
        }

        # Execute
        result = extract_issue_details(msg_data)

        # Assert
        assert result["jira_id"] == "PROJ-123"
        assert result["jira_url"] is None  # URL should be None as there's no URL in the text
        assert result["title"] == msg_data["title"]
        assert result["description"] == msg_data["description"]

    @patch('app.services.msg_parser.extract_msg.Message')
    @patch('app.services.msg_parser.os.path.exists')
    @patch('app.services.msg_parser.os.makedirs')  # Add makedirs mock
    def test_parse_msg_file_with_invalid_header(self, mock_makedirs, mock_exists, mock_message_class):
        # Setup
        mock_msg = MagicMock()
        mock_msg.subject = "Test Subject"
        mock_msg.sender = "test@example.com"
        mock_msg.body = "Test body"
        mock_msg.to = "recipient@example.com"
        mock_msg.date = datetime.now()
        mock_msg.header = 123  # Invalid header type
        mock_msg.attachments = []
        mock_msg.close = MagicMock()  # Add close method mock
        
        mock_exists.return_value = True
        mock_message_class.return_value = mock_msg
        mock_makedirs.return_value = None  # Mock successful directory creation

        # Execute
        result = parse_msg_file("/path/to/test.msg")

        # Assert
        assert isinstance(result["headers"], dict)
        assert "raw_header" in result["headers"]
        assert result["headers"]["raw_header"] == "123"
        mock_makedirs.assert_called_once()
        mock_msg.close.assert_called_once()

    def test_extract_issue_details_with_jira_url(self):
        # Setup
        msg_data = {
            "subject": "Service Issue",
            "body": "Please check https://jira.company.com/browse/PROJ-123 for details"
        }

        # Execute
        result = extract_issue_details(msg_data)

        # Assert
        assert result["jira_id"] == "PROJ-123"
        assert result["jira_url"] == "https://jira.company.com/browse/PROJ-123"

    def test_extract_issue_details_no_jira_info(self):
        # Setup
        msg_data = {
            "subject": "General Issue",
            "body": "This is a general issue without any Jira reference"
        }

        # Execute
        result = extract_issue_details(msg_data)

        # Assert
        assert result["jira_id"] is None
        assert result["jira_url"] is None
        assert result["title"] == msg_data["subject"]
        assert result["description"] == msg_data["body"]
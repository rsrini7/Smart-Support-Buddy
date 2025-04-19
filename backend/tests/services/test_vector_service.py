import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import numpy as np

import app.services.vector_service as vector_service
from app.services.embedding_service import get_embedding_model

class TestVectorService:
    @pytest.fixture
    def mock_msg_data(self):
        return {
            "subject": "Test Issue",
            "body": "Test body content",
            "sender": "test@example.com",
            "received_date": datetime.now(),
            "jira_id": "PROJ-123",
            "jira_url": "https://jira.company.com/browse/PROJ-123",
            "recipients": ["recipient@example.com"],
            "attachments": ["test.txt"],
            "file_path": "/path/to/test.msg"
        }

    @pytest.fixture
    def mock_jira_data(self):
        return {
            "key": "PROJ-123",
            "summary": "Test Jira Issue",
            "description": "Test description",
            "comments": [
                {"author": {"displayName": "Test User"}, "body": "Test comment"}
            ]
        }

    @patch('app.services.vector_service.original_add_issue_to_vectordb')
    def test_add_issue_to_vectordb(self, mock_add_issue_to_vectordb, mock_msg_data, mock_jira_data):
        mock_add_issue_to_vectordb.return_value = 'issue_20230101120000_test.msg'
        result = vector_service.add_issue_to_vectordb(mock_msg_data, mock_jira_data)
        assert isinstance(result, str)
        assert result.startswith("issue_")
        mock_add_issue_to_vectordb.assert_called_once_with(mock_msg_data, mock_jira_data)

    @patch('app.services.vector_service.real_delete_issue')
    def test_delete_issue(self, mock_delete_issue):
        mock_delete_issue.return_value = True
        result = vector_service.delete_issue("test_issue_id")
        assert result is True
        mock_delete_issue.assert_called_once_with("test_issue_id")

    @patch('app.services.vector_service.real_get_issue')
    def test_get_issue(self, mock_get_issue):
        mock_issue = MagicMock()
        mock_issue.id = "test_issue_id"
        mock_issue.title = "Test Subject"
        mock_get_issue.return_value = mock_issue
        result = vector_service.get_issue("test_issue_id")
        assert result is not None
        assert result.id == "test_issue_id"
        assert result.title == "Test Subject"
        mock_get_issue.assert_called_once_with("test_issue_id")

    @patch('app.services.vector_service.real_search_similar_issues')
    def test_search_similar_issues(self, mock_search_similar_issues):
        mock_search_similar_issues.return_value = [
            MagicMock(id="test_issue_1", similarity_score=1.0),
            MagicMock(id="test_issue_2", similarity_score=0.9)
        ]
        results = vector_service.search_similar_issues("test query")
        assert isinstance(results, list)
        assert len(results) == 2
        assert results[0].id == "test_issue_1"
        assert results[1].id == "test_issue_2"
        assert results[0].similarity_score == 1.0
        assert results[1].similarity_score == 0.9
        mock_search_similar_issues.assert_called_once_with("test query", None, 10)

    @patch('app.services.vector_service.real_clear_collection')
    def test_clear_collection(self, mock_clear_collection):
        mock_clear_collection.return_value = True
        result = vector_service.clear_collection("test_collection")
        assert result is True
        mock_clear_collection.assert_called_once_with("test_collection")
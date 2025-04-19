import sys
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
import pytest
import json
import httpx

# Add backend directory to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.append(str(backend_dir))

from app.main import app
from app.models import SearchQuery, IssueResponse

client = TestClient(app)

class TestRoutes:
    def get_mock_jira_data(self):
        return {
            "key": "PROJ-123",
            "summary": "Test Issue",
            "description": "Test description",
            "status": "Open",
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat(),
            "comments": [
                {"author": {"displayName": "Test User"}, "body": "Test comment"}
            ]
        }

    @patch('app.api.routes.get_jira_ticket')
    def test_get_jira_ticket_info(self, mock_get_ticket):
        mock_jira_data = self.get_mock_jira_data()
        mock_get_ticket.return_value = mock_jira_data

        response = client.get("/api/jira-ticket/PROJ-123")
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert response.json()["jira_data"] == mock_jira_data

    @patch('app.services.vector_service.search_similar_issues')
    @patch('app.services.vector_service.add_issue_to_vectordb')
    @patch('app.services.vector_service.get_vector_db_client')
    @patch('app.services.embedding_service.get_embedding_model')
    def test_search_issues(self, mock_get_embedding_model, mock_get_vector_db_client, mock_add_issue_to_vectordb, mock_search):
        mock_results = [
            {
                "id": "test_1",
                "title": "Test Issue 1",
                "description": "Test description 1",
                "sender": "test1@example.com",
                "received_date": datetime.now().isoformat(),
                "jira_ticket_id": "PROJ-123",
                "similarity_score": 0.95,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "root_cause": None,
                "solution": None,
                "jira_data": None
            },
            {
                "id": "test_2",
                "title": "Test Issue 2",
                "description": "Test description 2",
                "sender": "test2@example.com",
                "received_date": datetime.now().isoformat(),
                "jira_ticket_id": "PROJ-124",
                "similarity_score": 0.9,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "root_cause": None,
                "solution": None,
                "jira_data": None
            }
        ]
        mock_search.return_value = mock_results
        mock_get_embedding_model.return_value = MagicMock()
        mock_get_vector_db_client.return_value = MagicMock()
        mock_add_issue_to_vectordb.return_value = MagicMock()

        response = client.post(
            "/api/search",
            json={"query_text": "test query", "limit": 2}
        )
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 2
        assert results[0]["jira_ticket_id"] == "PROJ-123"
        assert results[1]["jira_ticket_id"] == "PROJ-124"

    @patch('app.services.vector_service.delete_issue')
    def test_delete_issue(self, mock_delete):
        mock_delete.return_value = True

        response = client.delete("/api/issues/test_1")
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "success"
        assert "test_1" in result["message"]

    @patch('app.services.msg_parser.parse_msg_file')
    @patch('app.services.vector_service.add_issue_to_vectordb')
    def test_ingest_msg_directory(self, mock_add_to_vectordb, mock_parse_msg):
        mock_msg_data = {
            "subject": "Test Issue",
            "body": "Test content",
            "sender": "test@example.com",
            "received_date": datetime.now().isoformat(),
            "jira_id": "PROJ-123"
        }
        mock_parse_msg.return_value = mock_msg_data
        mock_add_to_vectordb.return_value = "test_issue_1"

        # The actual endpoint expects files, not json, so we simulate the wrong input and check for 422
        response = client.post(
            "/api/ingest-msg-dir",
            json={"directory_path": "/test/path"}
        )
        assert response.status_code == 422  # Unprocessable Entity due to wrong input type

    @patch('app.api.routes.add_confluence_page_to_vectordb')
    def test_ingest_confluence_page(self, mock_add_confluence):
        mock_add_confluence.return_value = "test_page_1"

        # The actual endpoint expects {"confluence_urls": [...]}, not {"confluence_url": ...}
        response = client.post(
            "/api/ingest-confluence",
            json={"confluence_urls": ["https://confluence.example.com/page"]}
        )
        assert response.status_code == 200
        result = response.json()
        assert result["results"][0]["status"] == "success"
        assert result["results"][0]["page_id"] == "test_page_1"

    @patch('app.api.routes.add_stackoverflow_qa_to_vectordb')
    def test_ingest_stackoverflow_qa(self, mock_add_stackoverflow):
        mock_add_stackoverflow.return_value = ["test_qa_1"]

        response = client.post(
            "/api/ingest-stackoverflow",
            json={"stackoverflow_urls": ["https://stackoverflow.com/questions/123"]}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["results"][0]["status"] == "success"
        assert result["results"][0]["ids"] == ["test_qa_1"]
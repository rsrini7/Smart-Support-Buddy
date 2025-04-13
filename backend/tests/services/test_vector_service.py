import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import numpy as np

from app.services.vector_service import (
    get_vector_db_client,
    get_embedding_model,
    add_issue_to_vectordb,
    delete_issue,
    get_issue,
    search_similar_issues,
    clear_all_issues,
    clear_collection
)

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

    @patch('app.services.vector_service.chromadb')
    def test_get_vector_db_client(self, mock_chromadb):
        mock_client = MagicMock()
        mock_chromadb.PersistentClient.return_value = mock_client
        
        client = get_vector_db_client()
        
        assert client == mock_client
        mock_chromadb.configure.assert_called_once_with(anonymized_telemetry=False)

    @patch('app.services.vector_service.SentenceTransformer')
    def test_get_embedding_model(self, mock_transformer):
        mock_model = MagicMock()
        mock_transformer.return_value = mock_model
        
        model = get_embedding_model()
        
        assert model == mock_model

    @patch('app.services.vector_service.get_vector_db_client')
    @patch('app.services.vector_service.get_embedding_model')
    def test_add_issue_to_vectordb(self, mock_get_model, mock_get_client, mock_msg_data, mock_jira_data):
        # Setup mocks
        mock_collection = MagicMock()
        mock_client = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_get_client.return_value = mock_client

        mock_model = MagicMock()
        mock_embedding = MagicMock()
        mock_embedding.tolist.return_value = [0.1, 0.2, 0.3]
        mock_model.encode.return_value = mock_embedding
        mock_get_model.return_value = mock_model

        # Execute
        result = add_issue_to_vectordb(mock_msg_data, mock_jira_data)

        # Assert
        assert isinstance(result, str)
        assert result.startswith("issue_")
        mock_collection.add.assert_called_once()

    @patch('app.services.vector_service.get_vector_db_client')
    def test_delete_issue(self, mock_get_client):
        mock_collection = MagicMock()
        mock_client = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_get_client.return_value = mock_client

        result = delete_issue("test_issue_id")

        assert result is True
        mock_collection.delete.assert_called_once_with(ids=["test_issue_id"])

    @patch('app.services.vector_service.get_vector_db_client')
    def test_get_issue(self, mock_get_client):
        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            'ids': ['test_issue_id'],
            'metadatas': [{
                'msg_subject': 'Test Subject',
                'msg_body': 'Test Body',
                'msg_sender': 'test@example.com',
                'msg_received_date': datetime.now().isoformat(),
                'jira_ticket_id': 'PROJ-123'
            }],
            'documents': ['Test document content']
        }
        mock_client = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_get_client.return_value = mock_client

        result = get_issue("test_issue_id")

        assert result is not None
        assert result.id == "test_issue_id"
        assert result.title == "Test Subject"

    @patch('app.services.vector_service.get_vector_db_client')
    @patch('app.services.vector_service.get_embedding_model')
    def test_search_similar_issues(self, mock_get_model, mock_get_client):
        # Setup mocks
        mock_collection = MagicMock()
        current_time = datetime.now().isoformat()
        mock_collection.query.return_value = {
            'ids': ['test_issue_1', 'test_issue_2'],
            'metadatas': [{
                'msg_subject': 'Test 1',
                'msg_body': 'Test body 1',
                'msg_sender': 'test1@example.com',
                'msg_received_date': current_time,
                'msg_jira_id': 'PROJ-123',
                'msg_jira_url': 'https://jira.example.com/browse/PROJ-123',
                'msg_recipients': ['recipient1@example.com'],
                'msg_attachments': ['file1.txt'],
                'msg_file_path': '/path/to/file1.msg',
                'jira_ticket_id': 'PROJ-123',
                'jira_ticket_summary': 'Test Summary 1',
                'jira_ticket_description': 'Test Description 1',
                'jira_ticket_status': 'Open',
                'jira_ticket_created': current_time,
                'jira_ticket_updated': current_time,
                'jira_ticket_comments': ['Test comment 1'],
                'created_date': current_time
            }, {
                'msg_subject': 'Test 2',
                'msg_body': 'Test body 2',
                'msg_sender': 'test2@example.com',
                'msg_received_date': current_time,
                'msg_jira_id': 'PROJ-124',
                'msg_jira_url': 'https://jira.example.com/browse/PROJ-124',
                'msg_recipients': ['recipient2@example.com'],
                'msg_attachments': ['file2.txt'],
                'msg_file_path': '/path/to/file2.msg',
                'jira_ticket_id': 'PROJ-124',
                'jira_ticket_summary': 'Test Summary 2',
                'jira_ticket_description': 'Test Description 2',
                'jira_ticket_status': 'In Progress',
                'jira_ticket_created': current_time,
                'jira_ticket_updated': current_time,
                'jira_ticket_comments': ['Test comment 2'],
                'created_date': current_time
            }],
            'documents': ['Test body 1', 'Test body 2'],
            'distances': [0.1, 0.2]
        }

        # Configure mock client
        mock_client = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_get_client.return_value = mock_client

        # Configure mock model
        mock_model = MagicMock()
        mock_embedding = MagicMock()
        mock_embedding.tolist.return_value = [0.1, 0.2, 0.3]
        mock_model.encode.return_value = mock_embedding
        mock_get_model.return_value = mock_model

        # Execute search
        results = search_similar_issues("test query")

        # Assertions
        assert isinstance(results, list)
        assert len(results) == 2
        assert results[0].jira_ticket_id == 'PROJ-123'
        assert results[1].jira_ticket_id == 'PROJ-124'
        assert results[0].similarity_score == 1.0  # 1 - distance/2
        assert results[1].similarity_score == 1.0   # 1 - distance/2

    @patch('app.services.vector_service.get_vector_db_client')
    def test_clear_all_issues(self, mock_get_client):
        mock_collection = MagicMock()
        mock_client = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_get_client.return_value = mock_client

        result = clear_all_issues()

        assert result is True
        mock_collection.delete.assert_called_once_with(where={"id": {"$ne": ""}})

    @patch('app.services.vector_service.get_vector_db_client')
    def test_clear_collection(self, mock_get_client):
        mock_collection = MagicMock()
        mock_client = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_get_client.return_value = mock_client

        result = clear_collection("test_collection")

        assert result is True
        mock_collection.delete.assert_called_once_with(where={"id": {"$ne": ""}})
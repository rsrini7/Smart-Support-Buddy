import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.services.stackoverflow_service import (
    extract_question_id,
    fetch_stackoverflow_content,
    strip_html_tags,
    add_stackoverflow_qa_to_vectordb,
    search_similar_stackoverflow_content,
    sanitize_metadata
)

class TestStackOverflowService:
    
    def test_extract_question_id_valid_url(self):
        url = "https://stackoverflow.com/questions/12345678/sample-question"
        assert extract_question_id(url) == "12345678"

    def test_extract_question_id_invalid_url(self):
        url = "https://stackoverflow.com/invalid/url"
        assert extract_question_id(url) is None

    def test_strip_html_tags(self):
        html = "<p>Test content</p><code>some code</code>"
        assert strip_html_tags(html) == "Test content\nsome code"

    def test_sanitize_metadata(self):
        metadata = {
            "key1": None,
            "key2": ["item1", "item2"],
            "key3": "value3"
        }
        expected = {
            "key1": "",
            "key2": "item1, item2",
            "key3": "value3"
        }
        assert sanitize_metadata(metadata) == expected

    @patch('app.services.stackoverflow_service.requests.get')
    def test_fetch_stackoverflow_content(self, mock_get):
        # Mock responses for both API calls
        mock_question_response = MagicMock()
        mock_question_response.json.return_value = {
            "items": [{
                "title": "Sample Question",
                "body": "<p>Question body</p>",
                "question_id": "12345678"
            }]
        }

        mock_answers_response = MagicMock()
        mock_answers_response.json.return_value = {
            "items": [{
                "answer_id": 87654321,
                "body": "<p>Answer body</p>",
                "is_accepted": True,
                "score": 5
            }]
        }

        mock_get.side_effect = [mock_question_response, mock_answers_response]

        result = fetch_stackoverflow_content("https://stackoverflow.com/questions/12345678/sample-question")
        
        assert result is not None
        assert result["question_id"] == "12345678"
        assert result["question_title"] == "Sample Question"
        assert len(result["answers"]) == 1
        assert result["answers"][0]["answer_id"] == 87654321

    @patch('app.services.stackoverflow_service.get_vector_db_client')
    @patch('app.services.stackoverflow_service.get_embedding_model')
    @patch('app.services.stackoverflow_service.fetch_stackoverflow_content')
    def test_add_stackoverflow_qa_to_vectordb(self, mock_fetch, mock_model, mock_client):
        # Mock the fetch content response
        mock_fetch.return_value = {
            "question_id": "12345678",
            "question_title": "Sample Question",
            "question_text": "Question text",
            "question_url": "https://stackoverflow.com/questions/12345678",
            "answers": [{
                "answer_id": 87654321,
                "text": "Answer text",
                "is_accepted": True,
                "score": 5
            }]
        }

        # Mock the embedding model to return a numpy array with tolist method
        mock_embedding = MagicMock()
        mock_embedding.tolist.return_value = [0.1, 0.2, 0.3]
        mock_model.return_value.encode.return_value = mock_embedding

        # Mock the vector DB client
        mock_collection = MagicMock()
        mock_client.return_value.get_or_create_collection.return_value = mock_collection

        result = add_stackoverflow_qa_to_vectordb("https://stackoverflow.com/questions/12345678")
        
        assert result is not None
        assert len(result) == 2  # One for question, one for answer
        assert result[0].startswith("stackoverflow_q_")
        assert result[1].startswith("stackoverflow_a_")

    @patch('app.services.stackoverflow_service.get_vector_db_client')
    @patch('app.services.stackoverflow_service.get_embedding_model')
    def test_search_similar_stackoverflow_content(self, mock_model, mock_client):
        # Mock the embedding model to return a numpy array with tolist method
        mock_embedding = MagicMock()
        mock_embedding.tolist.return_value = [0.1, 0.2, 0.3]
        mock_model.return_value.encode.return_value = mock_embedding

        # Mock the vector DB client and collection
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            "ids": ["id1", "id2"],
            "metadatas": [{"type": "question"}, {"type": "answer"}],
            "documents": ["doc1", "doc2"],
            "distances": [0.1, 0.2]
        }
        mock_client.return_value.get_or_create_collection.return_value = mock_collection

        result = search_similar_stackoverflow_content("test query")
        
        assert result is not None
        assert "ids" in result
        assert "metadatas" in result
        assert "documents" in result
        assert "distances" in result
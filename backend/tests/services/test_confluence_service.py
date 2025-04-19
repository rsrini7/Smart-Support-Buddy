import pytest
from unittest.mock import patch, MagicMock
import chromadb
from datetime import datetime
import numpy as np

import app.services.confluence_service as confluence_service
from app.services.embedding_service import get_embedding_model

class TestConfluenceService:
    
    @patch('app.services.confluence_service.get_vector_db_client')
    @patch('app.services.confluence_service.get_embedding_model')
    def test_get_vector_db_client(self, mock_get_embedding_model, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_get_embedding_model.return_value = MagicMock()
        result = confluence_service.get_vector_db_client()
        assert result == mock_client
        mock_get_client.assert_called_once()

    @patch('app.services.confluence_service.get_embedding_model')
    def test_get_embedding_model(self, mock_get_embedding_model):
        mock_model = MagicMock()
        mock_get_embedding_model.return_value = mock_model
        result = confluence_service.get_embedding_model()
        assert result == mock_model
        mock_get_embedding_model.assert_called_once()

    @patch('app.services.confluence_service.requests.get')
    @patch('bs4.BeautifulSoup')
    def test_fetch_confluence_content_success(self, mock_bs, mock_get):
        mock_response = MagicMock()
        mock_response.text = "<html><body><div id='main-content'>Test Content</div></body></html>"
        mock_get.return_value = mock_response
        
        mock_soup = MagicMock()
        mock_main_content = MagicMock()
        mock_main_content.get_text.return_value = "Test Content"
        mock_soup.find.return_value = mock_main_content
        mock_bs.return_value = mock_soup
        
        mock_response.raise_for_status = MagicMock()
        
        result = confluence_service.fetch_confluence_content("https://confluence.example.com/page")
        
        assert result["content"] == "Test Content"
        mock_get.assert_called_once()
        assert mock_get.call_args[0][0] == "https://confluence.example.com/page"
        mock_response.raise_for_status.assert_called_once()
        mock_bs.assert_called_once_with(mock_response.text, "html.parser")
        mock_soup.find.assert_any_call("div", {"id": "main-content"})
        mock_main_content.get_text.assert_any_call(separator="\n", strip=True)

    @patch('app.services.confluence_service.requests.get')
    def test_fetch_confluence_content_error(self, mock_get):
        mock_get.side_effect = Exception("Connection error")
        
        result = confluence_service.fetch_confluence_content("https://confluence.example.com/page")
        
        assert result is None
        mock_get.assert_called_once()
        assert mock_get.call_args[0][0] == "https://confluence.example.com/page"

    @patch('app.services.confluence_service.fetch_confluence_content')
    @patch('app.services.confluence_service.get_vector_db_client')
    @patch('app.services.confluence_service.get_embedding_model')
    @patch('app.services.confluence_service.datetime')
    def test_add_confluence_page_to_vectordb_success(self, mock_datetime, mock_model, mock_client, mock_fetch):
        mock_fetch.return_value = {"content": "Test Content"}
        
        mock_collection = MagicMock()
        mock_collection.get.return_value = {"ids": []}  # Simulate no existing page
        mock_db_client = MagicMock()
        mock_db_client.get_or_create_collection.return_value = mock_collection
        mock_client.return_value = mock_db_client
        
        mock_embedding_model = MagicMock()
        mock_embedding_model.encode.return_value = np.array([0.1, 0.2, 0.3])
        mock_model.return_value = mock_embedding_model
        
        mock_now = MagicMock()
        mock_now.strftime.return_value = "20230101120000"
        mock_now.isoformat.return_value = "2023-01-01T12:00:00"
        mock_datetime.now.return_value = mock_now
        
        result = confluence_service.add_confluence_page_to_vectordb("https://confluence.example.com/page", {"key": "value"})
        
        assert result == "confluence_20230101120000"
        mock_fetch.assert_called_once_with("https://confluence.example.com/page")
        mock_client.assert_called_once()
        mock_model.assert_called_once()
        mock_embedding_model.encode.assert_called_once_with("Test Content")
        mock_db_client.get_or_create_collection.assert_called_once_with("confluence_pages")
        mock_collection.add.assert_called_once()
        
        add_call_args = mock_collection.add.call_args[1]
        assert add_call_args["ids"] == ["confluence_20230101120000"]
        assert len(add_call_args["embeddings"]) == 1
        assert add_call_args["metadatas"][0]["confluence_url"] == "https://confluence.example.com/page"
        assert add_call_args["metadatas"][0]["key"] == "value"
        assert add_call_args["documents"] == ["Test Content"]

    @patch('app.services.confluence_service.fetch_confluence_content')
    def test_add_confluence_page_to_vectordb_fetch_error(self, mock_fetch):
        mock_fetch.return_value = None
        
        result = confluence_service.add_confluence_page_to_vectordb("https://confluence.example.com/page")
        
        assert result is None
        mock_fetch.assert_called_once_with("https://confluence.example.com/page")

    @patch('app.services.confluence_service.get_vector_db_client')
    @patch('app.services.confluence_service.get_embedding_model')
    def test_search_similar_confluence_pages_success(self, mock_model, mock_client):
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            "ids": [["page1"]],
            "metadatas": [[{"confluence_url": "https://confluence.example.com/page1"}]],
            "documents": [["Test Content"]],
            "distances": [[0.05]]
        }
        
        mock_db_client = MagicMock()
        mock_db_client.get_or_create_collection.return_value = mock_collection
        mock_client.return_value = mock_db_client
        
        mock_embedding_model = MagicMock()
        mock_embedding_model.encode.return_value = np.array([0.1, 0.2, 0.3])
        mock_model.return_value = mock_embedding_model
        
        result = confluence_service.search_similar_confluence_pages("test query", 5)
        
        assert isinstance(result, list)
        assert result[0]["page_id"] == "page1"
        assert result[0]["metadata"]["confluence_url"] == "https://confluence.example.com/page1"
        mock_client.assert_called_once()
        mock_model.assert_called_once()
        mock_embedding_model.encode.assert_called_once_with("test query")
        mock_db_client.get_or_create_collection.assert_called_once_with("confluence_pages")
        mock_collection.query.assert_called_once()

    @patch('app.services.confluence_service.get_vector_db_client')
    def test_search_similar_confluence_pages_error(self, mock_client):
        mock_client.side_effect = Exception("Database error")
        
        result = confluence_service.search_similar_confluence_pages("test query")
        
        assert result is None
        mock_client.assert_called_once()

    @patch('app.services.confluence_service.get_vector_db_client')
    @patch('app.services.confluence_service.get_embedding_model')
    def test_search_similar_confluence_pages(self, mock_get_embedding_model, mock_get_client):
        # Mock the vector DB collection and query
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            "ids": ["mock_id"],
            "metadatas": [{"title": "Mock Page"}],
            "documents": ["Mock content"],
            "distances": [0.1]
        }
        mock_get_client.return_value.get_or_create_collection.return_value = mock_collection
        mock_get_embedding_model.return_value.encode.return_value = MagicMock(tolist=lambda: [0.1, 0.2, 0.3])

        from app.services.confluence_service import search_similar_confluence_pages
        result = search_similar_confluence_pages("mock query")
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["page_id"] == "mock_id"
        assert result[0]["title"] == "Mock Page" or result[0]["title"] == "Confluence Page"
        assert result[0]["content"] == "Mock content"
        assert "similarity_score" in result[0]
import pytest
from unittest.mock import patch, MagicMock
import chromadb
from datetime import datetime
import numpy as np

from app.services.confluence_service import (
    get_vector_db_client,
    get_embedding_model,
    fetch_confluence_content,
    add_confluence_page_to_vectordb,
    search_similar_confluence_pages
)


class TestConfluenceService:
    
    @patch('app.services.confluence_service.chromadb')
    def test_get_vector_db_client(self, mock_chromadb):
        # Setup mock
        mock_client = MagicMock()
        mock_chromadb.PersistentClient.return_value = mock_client
        
        # Call the function
        result = get_vector_db_client()
        
        # Assertions
        assert result == mock_client
        mock_chromadb.configure.assert_called_once_with(anonymized_telemetry=False)
        mock_chromadb.PersistentClient.assert_called_once()
    
    @patch('app.services.confluence_service.SentenceTransformer')
    def test_get_embedding_model(self, mock_transformer):
        # Setup mock
        mock_model = MagicMock()
        mock_transformer.return_value = mock_model
        
        # Call the function
        result = get_embedding_model()
        
        # Assertions
        assert result == mock_model
        mock_transformer.assert_called_once()
    
    @patch('app.services.confluence_service.requests.get')
    @patch('bs4.BeautifulSoup')
    def test_fetch_confluence_content_success(self, mock_bs, mock_get):
        # Setup mocks
        mock_response = MagicMock()
        mock_response.text = "<html><body><div id='main-content'>Test Content</div></body></html>"
        mock_get.return_value = mock_response
        
        mock_soup = MagicMock()
        mock_main_content = MagicMock()
        mock_main_content.get_text.return_value = "Test Content"
        mock_soup.find.return_value = mock_main_content
        mock_bs.return_value = mock_soup
        
        # Call the function
        result = fetch_confluence_content("https://confluence.example.com/page")
        
        # Assertions
        assert result == "Test Content"
        mock_get.assert_called_once_with("https://confluence.example.com/page")
        mock_response.raise_for_status.assert_called_once()
        mock_bs.assert_called_once_with(mock_response.text, "html.parser")
        mock_soup.find.assert_called_once_with("div", {"id": "main-content"})
        mock_main_content.get_text.assert_called_once_with(separator="\n", strip=True)
    
    @patch('app.services.confluence_service.requests.get')
    def test_fetch_confluence_content_error(self, mock_get):
        # Setup mock to raise exception
        mock_get.side_effect = Exception("Connection error")
        
        # Call the function
        result = fetch_confluence_content("https://confluence.example.com/page")
        
        # Assertions
        assert result is None
        mock_get.assert_called_once_with("https://confluence.example.com/page")
    
    @patch('app.services.confluence_service.fetch_confluence_content')
    @patch('app.services.confluence_service.get_vector_db_client')
    @patch('app.services.confluence_service.get_embedding_model')
    @patch('app.services.confluence_service.datetime')
    def test_add_confluence_page_to_vectordb_success(self, mock_datetime, mock_model, mock_client, mock_fetch):
        # Setup mocks
        mock_fetch.return_value = "Test Content"
        
        mock_collection = MagicMock()
        mock_db_client = MagicMock()
        mock_db_client.get_or_create_collection.return_value = mock_collection
        mock_client.return_value = mock_db_client
        
        mock_embedding_model = MagicMock()
        # Create a numpy array that has tolist() method
        mock_embedding_model.encode.return_value = np.array([0.1, 0.2, 0.3])
        mock_model.return_value = mock_embedding_model
        
        # Mock datetime
        mock_now = MagicMock()
        mock_now.strftime.return_value = "20230101120000"
        mock_now.isoformat.return_value = "2023-01-01T12:00:00"
        mock_datetime.now.return_value = mock_now
        
        # Call the function
        result = add_confluence_page_to_vectordb("https://confluence.example.com/page", {"key": "value"})
        
        # Assertions
        assert result == "confluence_20230101120000"
        mock_fetch.assert_called_once_with("https://confluence.example.com/page")
        mock_client.assert_called_once()
        mock_model.assert_called_once()
        mock_embedding_model.encode.assert_called_once_with("Test Content")
        mock_db_client.get_or_create_collection.assert_called_once_with("confluence_pages")
        mock_collection.add.assert_called_once()
        
        # Check the arguments passed to collection.add
        add_call_args = mock_collection.add.call_args[1]
        assert add_call_args["ids"] == ["confluence_20230101120000"]
        assert len(add_call_args["embeddings"]) == 1
        assert add_call_args["metadatas"][0]["confluence_url"] == "https://confluence.example.com/page"
        assert add_call_args["metadatas"][0]["key"] == "value"
        assert add_call_args["documents"] == ["Test Content"]
    
    @patch('app.services.confluence_service.fetch_confluence_content')
    def test_add_confluence_page_to_vectordb_fetch_error(self, mock_fetch):
        # Setup mock to return None (fetch failure)
        mock_fetch.return_value = None
        
        # Call the function
        result = add_confluence_page_to_vectordb("https://confluence.example.com/page")
        
        # Assertions
        assert result is None
        mock_fetch.assert_called_once_with("https://confluence.example.com/page")
    
    @patch('app.services.confluence_service.get_vector_db_client')
    @patch('app.services.confluence_service.get_embedding_model')
    def test_search_similar_confluence_pages_success(self, mock_model, mock_client):
        # Setup mocks
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            "ids": [["page1"]],
            "metadatas": [[{"confluence_url": "https://confluence.example.com/page1"}]],
            "documents": [["Test Content"]],
            "distances": [[0.1]]
        }
        
        mock_db_client = MagicMock()
        mock_db_client.get_or_create_collection.return_value = mock_collection
        mock_client.return_value = mock_db_client
        
        mock_embedding_model = MagicMock()
        # Create a numpy array that has tolist() method
        mock_embedding_model.encode.return_value = np.array([0.1, 0.2, 0.3])
        mock_model.return_value = mock_embedding_model
        
        # Call the function
        result = search_similar_confluence_pages("test query", 5)
        
        # Assertions
        assert result is not None
        assert result["ids"] == [["page1"]]
        assert result["metadatas"] == [[{"confluence_url": "https://confluence.example.com/page1"}]]
        mock_client.assert_called_once()
        mock_model.assert_called_once()
        mock_embedding_model.encode.assert_called_once_with("test query")
        mock_db_client.get_or_create_collection.assert_called_once_with("confluence_pages")
        mock_collection.query.assert_called_once()
    
    @patch('app.services.confluence_service.get_vector_db_client')
    def test_search_similar_confluence_pages_error(self, mock_client):
        # Setup mock to raise exception
        mock_client.side_effect = Exception("Database error")
        
        # Call the function
        result = search_similar_confluence_pages("test query")
        
        # Assertions
        assert result is None
        mock_client.assert_called_once()
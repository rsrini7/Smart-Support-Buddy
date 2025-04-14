import logging
import hashlib
import requests
from typing import Optional, Dict, Any
from datetime import datetime
from sentence_transformers import SentenceTransformer
import chromadb

from app.core.config import settings

logger = logging.getLogger(__name__)

def get_vector_db_client():
    try:
        chromadb.configure(anonymized_telemetry=False)
        client = chromadb.PersistentClient(path=settings.VECTOR_DB_PATH)
        return client
    except Exception as e:
        logger.error(f"Error initializing vector database client: {str(e)}")
        raise

def get_embedding_model():
    try:
        model = SentenceTransformer(settings.EMBEDDING_MODEL)
        return model
    except Exception as e:
        logger.error(f"Error initializing embedding model: {str(e)}")
        raise

def fetch_confluence_content(confluence_url: str) -> Optional[str]:
    """
    Fetch the main content from a Confluence page.
    This is a simple implementation that fetches the HTML and extracts the main content.
    For production, use Confluence REST API or a proper HTML parser.
    """
    try:
        response = requests.get(confluence_url)
        response.raise_for_status()
        # Simple extraction: get all text (for demo; improve with BeautifulSoup if needed)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")
        # Try to extract the main content area
        main_content = soup.find("div", {"id": "main-content"})
        if not main_content:
            main_content = soup.body
        text = main_content.get_text(separator="\n", strip=True) if main_content else soup.get_text(separator="\n", strip=True)
        return text
    except Exception as e:
        logger.error(f"Error fetching Confluence content: {str(e)}")
        return None

def add_confluence_page_to_vectordb(confluence_url: str, extra_metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """
    Fetch a Confluence page, embed its content, and store in ChromaDB.
    """
    try:
        content = fetch_confluence_content(confluence_url)
        if not content:
            raise ValueError("Failed to fetch content from Confluence URL")

        client = get_vector_db_client()
        model = get_embedding_model()

        # Compute deduplication hash (content only, since title is not available)
        content_hash = hashlib.sha256((content or "").encode("utf-8")).hexdigest()

        collection = client.get_or_create_collection("confluence_pages")
        # Check for existing page with same content hash
        existing = collection.get(where={"content_hash": content_hash})
        if existing and existing.get("ids"):
            # Return existing id, skip duplicate add
            return existing["ids"][0]

        # Create a unique ID for the page
        page_id = f"confluence_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        embedding = model.encode(content).tolist()

        metadata = {
            "confluence_url": confluence_url,
            "created_date": datetime.now().isoformat(),
            "content_hash": content_hash
        }
        if extra_metadata:
            metadata.update(extra_metadata)

        # Sanitize metadata
        sanitized_metadata = {}
        for k, v in metadata.items():
            if v is None:
                sanitized_metadata[k] = ""
            elif isinstance(v, list):
                sanitized_metadata[k] = ", ".join(str(item) for item in v)
            else:
                sanitized_metadata[k] = v
        metadata = sanitized_metadata

        collection.add(
            ids=[page_id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[content]
        )
        return page_id
    except Exception as e:
        logger.error(f"Error adding Confluence page to vector database: {str(e)}")
        return None

def search_similar_confluence_pages(query_text: str, limit: int = 10):
    """
    Search for similar Confluence pages based on a query.
    """
    try:
        client = get_vector_db_client()
        collection = client.get_or_create_collection("confluence_pages")
        model = get_embedding_model()
        query_embedding = model.encode(query_text).tolist()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            include=['metadatas', 'documents', 'distances']
        )
        # Defensive fix: if results is a list, convert to empty dict structure
        if isinstance(results, list):
            results = {"ids": [], "metadatas": [], "documents": [], "distances": []}

        # Format results as a list of objects for the frontend
        formatted = []
        ids = results.get("ids", [])
        metadatas = results.get("metadatas", [])
        documents = results.get("documents", [])
        distances = results.get("distances", [])

        # Handle possible nested lists from ChromaDB
        if ids and isinstance(ids[0], list):
            ids = ids[0]
        if metadatas and isinstance(metadatas[0], list):
            metadatas = metadatas[0]
        if documents and isinstance(documents[0], list):
            documents = documents[0]
        if distances and isinstance(distances[0], list):
            distances = distances[0]

        seen = set()
        for i, page_id in enumerate(ids):
            metadata = metadatas[i] if i < len(metadatas) else {}
            document = documents[i] if i < len(documents) else ""
            confluence_url = metadata.get("confluence_url", "")
            unique_key = (str(page_id), confluence_url, document)
            if unique_key in seen:
                continue
            seen.add(unique_key)
            distance = distances[i] if i < len(distances) else 0.0
            similarity_score = 1.0 - min(distance / 2, 1.0)
            logger.info(f"Similarity threshold: {settings.SIMILARITY_THRESHOLD}, Calculated similarity: {similarity_score:.6f} for Page ID: {page_id}")
            if similarity_score < settings.SIMILARITY_THRESHOLD:
                continue  # Skip results below threshold
            formatted.append({
                "page_id": page_id,
                "title": confluence_url or "Confluence Page",
                "content": document,
                "similarity_score": similarity_score,
                "metadata": metadata
            })
        return formatted
    except Exception as e:
        logger.error(f"Error searching similar Confluence pages: {str(e)}")
        return None
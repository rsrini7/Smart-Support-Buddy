from typing import Optional, Dict, Any
from app.services.chroma_client import get_collection
from app.services.embedding_service import get_embedding
from app.services.deduplication_utils import compute_content_hash
from app.services.confluence_service import fetch_confluence_content
from app.utils.similarity import compute_similarity_score
from app.models.models import ConfluencePage
import logging
from datetime import datetime

# DEPRECATION WARNING: This service is deprecated and not used by any API routes. Please remove after migration verification.
# All ingestion should use app.services.confluence_service.add_confluence_page_to_vectordb which uses the unified index_vector_data utility.

logger = logging.getLogger(__name__)

COLLECTION_NAME = "confluence_pages"

def add_confluence_page_to_vectordb_with_aug(
    confluence_url: str,
    extra_metadata: Optional[Dict[str, Any]] = None,
    llm_augment: Optional[Any] = None,
    augment_metadata: bool = True,
    normalize_language: bool = True,
    target_language: str = "en"
) -> Optional[str]:
    """
    Wrapper to call the new add_confluence_page_to_vectordb with augmentation options.
    """
    return add_confluence_page_to_vectordb(
        confluence_url=confluence_url,
        extra_metadata=extra_metadata,
        llm_augment=llm_augment,
        augment_metadata=augment_metadata,
        normalize_language=normalize_language,
        target_language=target_language
    )

def add_confluence_page_to_vectordb(
    confluence_url: str, extra_metadata: Optional[Dict[str, Any]] = None, llm_augment: Optional[Any] = None, augment_metadata: bool = True, normalize_language: bool = True, target_language: str = "en"
) -> Optional[str]:
    # DEPRECATION WARNING: This function is deprecated and not used by any API routes. Please remove after migration verification.
    try:
        content = fetch_confluence_content(confluence_url)
        if not content:
            raise ValueError("Failed to fetch content from Confluence URL")
        collection = get_collection(COLLECTION_NAME)
        embedding = get_embedding(content)
        content_hash = compute_content_hash(content or "")
        # Check for existing page
        existing = collection.get(where={"content_hash": content_hash})
        if existing and existing.get("ids"):
            return existing["ids"][0]
        page_id = f"confluence_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        metadata = extra_metadata or {}
        metadata["content_hash"] = content_hash
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
    try:
        collection = get_collection(COLLECTION_NAME)
        embedding = get_embedding(query_text)
        results = collection.query(
            query_embeddings=[embedding],
            n_results=limit,
            include=['metadatas', 'documents', 'distances']
        )
        formatted = []
        ids = results.get("ids", [])[0] if results.get("ids") else []
        metadatas = results.get("metadatas", [])[0] if results.get("metadatas") else []
        documents = results.get("documents", [])[0] if results.get("documents") else []
        distances = results.get("distances", [])[0] if results.get("distances") else []
        for i, page_id in enumerate(ids):
            metadata = metadatas[i] if i < len(metadatas) else {}
            document = documents[i] if i < len(documents) else ""
            distance = distances[i] if i < len(distances) else 0.0
            similarity_score = compute_similarity_score(distance)
            if similarity_score < 0.1:  # TODO: Use settings.SIMILARITY_THRESHOLD
                continue
            # Use ConfluencePage model for structured metadata
            page_obj = ConfluencePage(
                page_id=page_id,
                title=metadata.get('title', ''),
                url=metadata.get('url', ''),
                space=metadata.get('space'),
                labels=metadata.get('labels'),
                creator=metadata.get('creator'),
                created=metadata.get('created'),
                updated=metadata.get('updated'),
                content=document,
                similarity_score=similarity_score,
                metadata=metadata
            )
            formatted.append(page_obj.model_dump())
        return formatted
    except Exception as e:
        logger.error(f"Error searching similar Confluence pages: {str(e)}")
        return None

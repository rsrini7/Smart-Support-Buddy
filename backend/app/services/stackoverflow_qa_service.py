from typing import Optional, Dict, Any, List
from app.services.chroma_client import get_collection
from app.services.embedding_service import get_embedding_model
from app.utils.rag_utils import index_vector_data
from app.utils.llm_augmentation import llm_summarize
from app.services.deduplication_utils import compute_content_hash
from app.services.stackoverflow_service import fetch_stackoverflow_content
from app.models.models import StackOverflowQA
import logging
from datetime import datetime

# DEPRECATION WARNING: This service is deprecated and not used by any API routes. Please remove after migration verification.
# All ingestion should use app.services.stackoverflow_service.add_stackoverflow_qa_to_vectordb which uses the unified index_vector_data utility.

logger = logging.getLogger(__name__)

COLLECTION_NAME = "stackoverflow_qa"

def add_stackoverflow_qa_to_vectordb(
    stackoverflow_url: str,
    extra_metadata: Optional[Dict[str, Any]] = None,
    llm_augment: Optional[Any] = None,
    augment_metadata: bool = False,
    normalize_language: bool = False,
    target_language: str = "en"
) -> Optional[List[str]]:
    # DEPRECATION WARNING: This function is deprecated and not used by any API routes. Please remove after migration verification.
    try:
        content = fetch_stackoverflow_content(stackoverflow_url)
        if not content:
            raise ValueError("Failed to fetch content from Stack Overflow URL")
        client = get_collection(COLLECTION_NAME)._client
        embedder = get_embedding_model()
        ids, documents, metadatas = [], [], []
        # Add question
        question_id = content["question_id"]
        question_hash = compute_content_hash(content["question_text"])
        qid = f"soq_{question_id}"
        question_obj = StackOverflowQA(
            question_id=question_id,
            question_text=content["question_text"],
            tags=content.get("tags"),
            author=content.get("author"),
            creation_date=content.get("creation_date"),
            score=content.get("score"),
            link=content.get("link"),
            content_hash=question_hash,
            metadata=extra_metadata,
        )
        ids.append(qid)
        documents.append(content["question_text"])
        metadatas.append(question_obj.model_dump())
        # Add answers
        for ans in content.get("answers", []):
            aid = f"soa_{ans['answer_id']}"
            ans_hash = compute_content_hash(ans["text"])
            answer_obj = StackOverflowQA(
                question_id=ans["question_id"],
                question_text=ans["text"],
                tags=None,
                author=ans.get("author"),
                creation_date=ans.get("creation_date"),
                score=ans.get("score"),
                link=None,
                content_hash=ans_hash,
                metadata=None,
            )
            ids.append(aid)
            documents.append(ans["text"])
            metadatas.append(answer_obj.model_dump())
        # Use unified ingest utility with configurable augmentation
        index_vector_data(
            client=client,
            embedder=embedder,
            documents=documents,
            doc_ids=ids,
            collection_name=COLLECTION_NAME,
            metadatas=metadatas,
            clear_existing=False,
            deduplicate=True,
            llm_augment=llm_augment or llm_summarize,
            augment_metadata=augment_metadata,
            normalize_language=normalize_language,
            target_language=target_language
        )
        return ids
    except Exception as e:
        logger.error(f"Error adding Stack Overflow Q&A to vector database: {str(e)}")
        return None

def search_similar_stackoverflow_content(query_text: str, limit: int = 10):
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
        for i, so_id in enumerate(ids):
            metadata = metadatas[i] if i < len(metadatas) else {}
            document = documents[i] if i < len(documents) else ""
            distance = distances[i] if i < len(distances) else 0.0
            similarity_score = compute_similarity_score(distance)
            if similarity_score < settings.SIMILARITY_THRESHOLD:
                continue
            formatted.append({
                "id": so_id,
                "content": document,
                "similarity_score": similarity_score,
                "metadata": metadata
            })
        return formatted
    except Exception as e:
        logger.error(f"Error searching similar Stack Overflow content: {str(e)}")
        return None

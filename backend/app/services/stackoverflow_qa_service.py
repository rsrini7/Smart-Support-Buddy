from typing import Optional, Dict, Any, List
from app.services.chroma_client import get_collection
from app.services.embedding_service import get_embedding
from app.services.deduplication_utils import compute_content_hash
from app.services.stackoverflow_service import fetch_stackoverflow_content
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

COLLECTION_NAME = "stackoverflow_qa"

def add_stackoverflow_qa_to_vectordb(stackoverflow_url: str, extra_metadata: Optional[Dict[str, Any]] = None) -> Optional[List[str]]:
    try:
        content = fetch_stackoverflow_content(stackoverflow_url)
        if not content:
            raise ValueError("Failed to fetch content from Stack Overflow URL")
        collection = get_collection(COLLECTION_NAME)
        ids = []
        embeddings = []
        metadatas = []
        documents = []
        # Add question
        question_id = content["question_id"]
        question_hash = compute_content_hash(content["question_text"])
        existing_q = collection.get(where={"content_hash": question_hash})
        if existing_q and existing_q.get("ids"):
            ids.append(existing_q["ids"][0])
        else:
            qid = f"soq_{question_id}"
            ids.append(qid)
            embeddings.append(get_embedding(content["question_text"]))
            metadatas.append({"question_id": question_id, "content_hash": question_hash})
            documents.append(content["question_text"])
        # Add answers
        for ans in content.get("answers", []):
            ans_hash = compute_content_hash(ans["text"])
            existing_a = collection.get(where={"content_hash": ans_hash})
            if existing_a and existing_a.get("ids"):
                ids.append(existing_a["ids"][0])
            else:
                aid = f"soa_{ans["answer_id"]}"
                ids.append(aid)
                embeddings.append(get_embedding(ans["text"]))
                metadatas.append({"answer_id": ans["answer_id"], "content_hash": ans_hash})
                documents.append(ans["text"])
        # Only add if there are new documents
        if embeddings:
            collection.add(
                ids=ids[-len(embeddings):],
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
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
            similarity_score = 1.0 - min(distance / 2, 1.0)
            if similarity_score < 0.1:  # TODO: Use settings.SIMILARITY_THRESHOLD
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

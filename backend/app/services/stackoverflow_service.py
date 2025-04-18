import logging
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.services.chroma_client import get_vector_db_client
from app.services.embedding_service import get_embedding_model
import re
import requests

from app.core.config import settings

logger = logging.getLogger(__name__)

def extract_question_id(stackoverflow_url: str) -> Optional[str]:
    """
    Extract the question ID from a Stack Overflow URL.
    Example: https://stackoverflow.com/questions/12345678/title-text
    """
    try:
        match = re.search(r'/questions/(\d+)', stackoverflow_url)
        if match:
            return match.group(1)
        else:
            logger.error(f"Could not extract question ID from URL: {stackoverflow_url}")
            return None
    except Exception as e:
        logger.error(f"Error extracting question ID: {str(e)}")
        return None

def fetch_stackoverflow_content(stackoverflow_url: str) -> Optional[Dict[str, Any]]:
    """
    Fetch question and answers from Stack Exchange API for a given Stack Overflow URL.
    Returns a dict with question and answers as plain text.
    """
    try:
        question_id = extract_question_id(stackoverflow_url)
        if not question_id:
            raise ValueError("Invalid Stack Overflow URL or could not extract question ID.")

        # Fetch question
        api_url = f"https://api.stackexchange.com/2.3/questions/{question_id}?order=desc&sort=activity&site=stackoverflow&filter=withbody"
        resp = requests.get(api_url)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("items"):
            raise ValueError("No question found for the given ID.")

        question = data["items"][0]
        question_text = question.get("title", "") + "\n" + question.get("body", "")
        question_text = strip_html_tags(question_text)

        # Fetch answers
        answers_api_url = f"https://api.stackexchange.com/2.3/questions/{question_id}/answers?order=desc&sort=activity&site=stackoverflow&filter=withbody"
        answers_resp = requests.get(answers_api_url)
        answers_resp.raise_for_status()
        answers_data = answers_resp.json()
        answers = []
        for ans in answers_data.get("items", []):
            ans_text = ans.get("body", "")
            ans_text = strip_html_tags(ans_text)
            answers.append({
                "answer_id": ans.get("answer_id"),
                "text": ans_text,
                "is_accepted": ans.get("is_accepted", False),
                "score": ans.get("score", 0)
            })

        return {
            "question_id": question_id,
            "question_title": question.get("title", ""),
            "question_text": question_text,
            "question_url": stackoverflow_url,
            "answers": answers
        }
    except Exception as e:
        logger.error(f"Error fetching Stack Overflow content: {str(e)}")
        return None

def strip_html_tags(html: str) -> str:
    """
    Remove HTML tags from a string.
    """
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(separator="\n", strip=True)
    except Exception as e:
        logger.error(f"Error stripping HTML tags: {str(e)}")
        return html

def add_stackoverflow_qa_to_vectordb(stackoverflow_url: str, extra_metadata: Optional[Dict[str, Any]] = None) -> Optional[List[str]]:
    """
    Fetch Stack Overflow Q&A, embed question and answers, and store in ChromaDB.
    Returns list of added IDs.
    """
    try:
        content = fetch_stackoverflow_content(stackoverflow_url)
        if not content:
            raise ValueError("Failed to fetch content from Stack Overflow URL")

        client = get_vector_db_client()
        model = get_embedding_model()
        collection = client.get_or_create_collection("stackoverflow_qa")

        ids = []
        metadatas = []
        embeddings = []
        documents = []

        # Add question with deduplication
        q_id = f"stackoverflow_q_{content['question_id']}"
        q_hash_str = (content["question_title"] or "") + (content["question_text"] or "")
        q_content_hash = hashlib.sha256(q_hash_str.encode("utf-8")).hexdigest()
        # Check for existing question with same hash
        existing_q = collection.get(where={"content_hash": q_content_hash})
        if not (existing_q and existing_q.get("ids")):
            q_metadata = {
                "type": "question",
                "question_id": content["question_id"],
                "title": content["question_title"],
                "url": content["question_url"],
                "created_date": datetime.now().isoformat(),
                "content_hash": q_content_hash
            }
            if extra_metadata:
                q_metadata.update(extra_metadata)
            q_metadata = sanitize_metadata(q_metadata)
            q_embedding = model.encode(content["question_text"]).tolist()

            ids.append(q_id)
            metadatas.append(q_metadata)
            embeddings.append(q_embedding)
            documents.append(content["question_text"])
        else:
            # If duplicate, return existing question ID
            ids.append(existing_q["ids"][0])

        # Add answers with deduplication
        for ans in content["answers"]:
            a_id = f"stackoverflow_a_{ans['answer_id']}"
            a_hash_str = (ans["text"] or "") + str(content["question_id"])
            a_content_hash = hashlib.sha256(a_hash_str.encode("utf-8")).hexdigest()
            existing_a = collection.get(where={"content_hash": a_content_hash})
            if not (existing_a and existing_a.get("ids")):
                a_metadata = {
                    "type": "answer",
                    "question_id": content["question_id"],
                    "answer_id": ans["answer_id"],
                    "title": content["question_title"],
                    "url": content["question_url"],
                    "is_accepted": ans["is_accepted"],
                    "score": ans["score"],
                    "created_date": datetime.now().isoformat(),
                    "content_hash": a_content_hash
                }
                if extra_metadata:
                    a_metadata.update(extra_metadata)
                a_metadata = sanitize_metadata(a_metadata)
                a_embedding = model.encode(ans["text"]).tolist()

                ids.append(a_id)
                metadatas.append(a_metadata)
                embeddings.append(a_embedding)
                documents.append(ans["text"])
            else:
                # If duplicate, return existing answer ID
                ids.append(existing_a["ids"][0])

        # Only add if there are new documents to add
        if embeddings:
            collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
            )
        return ids
    except Exception as e:
        logger.error(f"Error adding Stack Overflow Q&A to vector database: {str(e)}")
        return None

def sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    sanitized = {}
    for k, v in metadata.items():
        if v is None:
            sanitized[k] = ""
        elif isinstance(v, list):
            sanitized[k] = ", ".join(str(item) for item in v)
        else:
            sanitized[k] = v
    return sanitized

def search_similar_stackoverflow_content(query_text: str, limit: int = 10):
    """
    Search for similar Stack Overflow Q&A based on a query.
    """
    try:
        client = get_vector_db_client()
        collection = client.get_or_create_collection("stackoverflow_qa")
        model = get_embedding_model()
        query_embedding = model.encode(query_text).tolist()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            include=['metadatas', 'documents', 'distances']
        )
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

        for i, so_id in enumerate(ids):
            metadata = metadatas[i] if i < len(metadatas) else {}
            document = documents[i] if i < len(documents) else ""
            distance = distances[i] if i < len(distances) else 0.0
            similarity_score = 1.0 - min(distance / 2, 1.0)
            logger.info(f"Similarity threshold: {settings.SIMILARITY_THRESHOLD}, Calculated similarity: {similarity_score:.6f} for StackOverflow ID: {so_id}")
            if similarity_score < settings.SIMILARITY_THRESHOLD:
                continue  # Skip results below threshold
            formatted.append({
                "id": so_id,
                "title": metadata.get("title", "Stack Overflow Q&A"),
                "content": document,
                "similarity_score": similarity_score,
                "metadata": metadata
            })
        return formatted
    except Exception as e:
        logger.error(f"Error searching similar Stack Overflow content: {str(e)}")
        return None
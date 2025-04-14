from typing import Dict, Any, Optional
from datetime import datetime, date
import os
import logging

from app.services.chroma_client import get_collection
from app.services.embedding_service import get_embedding
from app.services.deduplication_utils import compute_content_hash

logger = logging.getLogger(__name__)

COLLECTION_NAME = "production_issues"

def add_issue_to_vectordb(msg_data: Optional[Dict[str, Any]] = None, jira_data: Optional[Dict[str, Any]] = None) -> str:
    try:
        if msg_data is None:
            msg_data = {}
        if jira_data is None:
            jira_data = {}
        if not msg_data and not jira_data:
            raise ValueError("Either MSG data or Jira data must be provided")

        msg_subject = msg_data.get("subject", "")
        msg_body = msg_data.get("body", "")
        jira_ticket_id = jira_data.get("key") if jira_data else None
        jira_summary = jira_data.get("summary", "")
        jira_description = jira_data.get("description", "") or ""

        # Deduplication hash
        if msg_data:
            content_hash = compute_content_hash(msg_subject or "", msg_body or "")
        elif jira_data:
            content_hash = compute_content_hash(jira_summary or "", jira_description or "", jira_ticket_id or "")
        else:
            content_hash = ""

        collection = get_collection(COLLECTION_NAME)
        existing = collection.get(where={"content_hash": content_hash})
        if existing and existing.get("ids"):
            return existing["ids"][0]

        if msg_data:
            file_path = msg_data.get('file_path', '')
            suffix = os.path.basename(file_path) if file_path else 'no_msgfile'
            issue_id = f"issue_{datetime.now().strftime('%Y%m%d%H%M%S')}_{suffix}"
        elif jira_data:
            suffix = jira_ticket_id or 'no_jiraid'
            issue_id = f"issue_{datetime.now().strftime('%Y%m%d%H%M%S')}_{suffix}"
        else:
            issue_id = f"issue_{datetime.now().strftime('%Y%m%d%H%M%S')}_unknown"

        # Jira comments
        jira_comments_text = ""
        if jira_data:
            comments = jira_data.get("comments", [])
            if isinstance(comments, str):
                comments = [comments]
            elif not isinstance(comments, list):
                comments = []
            if comments:
                formatted_comments = []
                for comment in comments:
                    if isinstance(comment, dict):
                        author_field = comment.get("author", "Unknown Author")
                        if isinstance(author_field, dict):
                            author = author_field.get("displayName", "Unknown Author")
                        else:
                            author = author_field
                        body = comment.get("body", "")
                        formatted_comments.append(f"{author}: {body}")
                    else:
                        formatted_comments.append(str(comment))
                jira_comments_text = "\n".join(formatted_comments)

        # Prepare full text for embedding
        full_text = f"{msg_subject}\n{msg_body}\n{jira_summary}\n{jira_description}"
        if jira_comments_text:
            full_text += f"\nComments:\n{jira_comments_text}"
        embedding = get_embedding(full_text)

        metadata = {
            "msg_subject": msg_subject,
            "msg_body": msg_body,
            "msg_sender": msg_data.get("sender", "") if msg_data else "",
            "msg_received_date": "",
            "msg_jira_id": msg_data.get("jira_id", "") if msg_data else "",
            "msg_jira_url": msg_data.get("jira_url", "") if msg_data else "",
            "recipients": msg_data.get("recipients", []) if msg_data else [],
            "attachments": msg_data.get("attachments", []) if msg_data else [],
            "jira_ticket_id": jira_ticket_id or "",
            "jira_summary": jira_summary,
            "created_date": datetime.now().isoformat() if not (msg_data and msg_data.get("received_date")) else "",
            "content_hash": content_hash
        }
        # Safely assign msg_received_date
        received_date = msg_data.get("received_date", None) if msg_data else None
        if received_date:
            if isinstance(received_date, (datetime, date)):
                metadata["msg_received_date"] = received_date.isoformat()
            elif isinstance(received_date, str):
                metadata["msg_received_date"] = received_date
            else:
                metadata["msg_received_date"] = str(received_date)
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
            ids=[issue_id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[full_text]
        )
        return issue_id
    except Exception as e:
        logger.error(f"Error adding issue to vector database: {str(e)}")
        raise

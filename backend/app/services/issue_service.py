from typing import Optional, List, Dict, Any
from app.services.chroma_client import get_collection
from app.models import IssueResponse
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)

COLLECTION_NAME = "production_issues"

def delete_issue(issue_id: str) -> bool:
    try:
        collection = get_collection(COLLECTION_NAME)
        collection.delete(ids=[issue_id])
        return True
    except Exception as e:
        logger.error(f"Error deleting issue from vector database: {str(e)}")
        return False

def get_issue(issue_id: str) -> Optional[IssueResponse]:
    try:
        collection = get_collection(COLLECTION_NAME)
        result = collection.get(ids=[issue_id])
        if not result or not result['ids']:
            return None
        metadata = result['metadatas'][0]
        document = result['documents'][0]
        # Fetch Jira data if needed (optional)
        jira_data = None
        try:
            from app.services.jira_service import get_jira_ticket
            if isinstance(metadata, list):
                metadata = {}
            # FIX: Try both jira_ticket_id and msg_jira_id
            jira_ticket_id = metadata.get('jira_ticket_id') or metadata.get('msg_jira_id')
            if jira_ticket_id:
                jira_data = get_jira_ticket(jira_ticket_id)
        except Exception as e:
            logger.warning(f"Failed to fetch Jira data for ticket {metadata.get('jira_ticket_id') or metadata.get('msg_jira_id')}: {e}")
            jira_data = None
        return IssueResponse(
            id=issue_id,
            title=metadata.get('msg_subject', ''),
            description=document,
            jira_ticket_id=metadata.get('jira_ticket_id', '') or metadata.get('msg_jira_id', ''),
            received_date=metadata.get('msg_received_date', '') or metadata.get('created_date', ''),
            created_at=metadata.get('created_at') or metadata.get('created_date') or metadata.get('msg_received_date') or datetime.now(),
            updated_at=None,
            msg_data={
                'subject': metadata.get('msg_subject', ''),
                'body': metadata.get('msg_body', ''),
                'sender': metadata.get('msg_sender', ''),
                'received_date': metadata.get('msg_received_date', ''),
                'jira_id': metadata.get('msg_jira_id', ''),
                'jira_url': metadata.get('msg_jira_url', ''),
                'recipients': metadata.get('recipients', []),
                'attachments': metadata.get('attachments', [])
            },
            jira_data=jira_data
        )
    except Exception as e:
        logger.error(f"Error getting issue from vector database: {str(e)}")
        raise

def search_similar_issues(query_text: str = "", jira_ticket_id: Optional[str] = None, limit: int = 10) -> List[IssueResponse]:
    from app.services.embedding_service import get_embedding
    from app.core.config import settings
    try:
        collection = get_collection(COLLECTION_NAME)
        # If only Jira ticket ID is provided, use get() instead of query()
        if jira_ticket_id and not query_text:
            # FIX: Search both jira_ticket_id and msg_jira_id fields
            results = collection.get(
                where={"$and": [
                    {"$or": [
                        {"jira_ticket_id": jira_ticket_id.upper()},
                        {"jira_ticket_id": jira_ticket_id.lower()},
                        {"msg_jira_id": jira_ticket_id.upper()},
                        {"msg_jira_id": jira_ticket_id.lower()}
                    ]}
                ]},
                limit=limit,
            )
        else:
            query_embedding = get_embedding(query_text)
            query_params = {
                "query_embeddings": [query_embedding],
                "n_results": limit,
                "include": ['metadatas', 'documents', 'distances']
            }
            if jira_ticket_id:
                # FIX: Search both jira_ticket_id and msg_jira_id fields
                query_params["where"] = {"$and": [
                    {"$or": [
                        {"jira_ticket_id": jira_ticket_id.upper()},
                        {"jira_ticket_id": jira_ticket_id.lower()},
                        {"msg_jira_id": jira_ticket_id.upper()},
                        {"msg_jira_id": jira_ticket_id.lower()}
                    ]}
                ]}
            results = collection.query(**query_params)
        if isinstance(results, list):
            results = {"ids": [], "metadatas": [], "documents": [], "distances": []}
        issue_responses = []
        if results and len(results["ids"]) > 0:
            is_query_result = query_text and "distances" in results
            def flatten_if_nested(val):
                return val[0] if isinstance(val, list) and len(val) > 0 and isinstance(val[0], list) else val
            ids = flatten_if_nested(results.get("ids", []))
            metadatas = flatten_if_nested(results.get("metadatas", []))
            documents = flatten_if_nested(results.get("documents", []))
            distances = results.get("distances", [[0.0]])[0] if isinstance(results.get("distances", [[]])[0], list) else [0.0] * len(ids)
            for i, issue_id in enumerate(ids):
                if not isinstance(issue_id, str) or not issue_id:
                    continue
                metadata = metadatas[i]
                if isinstance(metadata, list):
                    metadata = {}
                document = documents[i]
                # --- JIRA ID BOOST LOGIC ---
                # If query is a JIRA ID and matches this record, set similarity_score to 1.0
                boost_jira_id = False
                if query_text:
                    jira_id_pattern = r"^[A-Z][A-Z0-9]+-\d+$"
                    if re.match(jira_id_pattern, query_text.strip(), re.IGNORECASE):
                        match_ids = [
                            (metadata.get("jira_ticket_id") or "").upper(),
                            (metadata.get("msg_jira_id") or "").upper()
                        ]
                        if query_text.strip().upper() in match_ids:
                            boost_jira_id = True
                if is_query_result:
                    if isinstance(distances, list) and len(distances) > i:
                        if isinstance(distances[0], list):
                            distance = distances[0][i]
                        else:
                            distance = distances[i]
                    else:
                        distance = 0.0
                    similarity_score = 1.0 - min(distance / 2, 1.0)
                    if boost_jira_id:
                        similarity_score = 1.0
                else:
                    distance = 0.0
                    similarity_score = 1.0
                received_date = None
                if metadata.get("msg_received_date"):
                    try:
                        received_date = datetime.fromisoformat(metadata["msg_received_date"])
                    except:
                        pass
                msg_data = {
                    'subject': metadata.get('msg_subject', ''),
                    'body': metadata.get('msg_body', ''),
                    'sender': metadata.get('msg_sender', ''),
                    'received_date': metadata.get('msg_received_date', ''),
                    'jira_id': metadata.get('msg_jira_id', ''),
                    'jira_url': metadata.get('msg_jira_url', ''),
                    'recipients': metadata.get('recipients', []),
                    'attachments': metadata.get('attachments', [])
                }
                issue_response = IssueResponse(
                    id=issue_id,
                    title=metadata.get("msg_subject") or metadata.get("jira_summary") or metadata.get("jira_ticket_id") or "Unknown Issue",
                    description=document,
                    jira_ticket_id=metadata.get("jira_ticket_id") or metadata.get("msg_jira_id"),
                    jira_data=None,
                    sender=metadata.get("msg_sender"),
                    received_date=metadata.get("msg_received_date", "") or metadata.get("created_date", ""),
                    created_at=datetime.now(),
                    updated_at=None,
                    similarity_score=similarity_score,
                    msg_data=msg_data
                )
                issue_responses.append(issue_response)
        issue_responses = [resp for resp in issue_responses if resp.similarity_score >= settings.SIMILARITY_THRESHOLD]
        issue_responses.sort(key=lambda x: getattr(x, 'similarity_score', 0), reverse=True)
        return issue_responses
    except Exception as e:
        logger.error(f"Error searching similar issues: {str(e)}")
        return []

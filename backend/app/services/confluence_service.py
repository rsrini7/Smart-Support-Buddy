import logging
import hashlib
import requests
from typing import Optional, Dict, Any
from datetime import datetime
from sentence_transformers import SentenceTransformer
import chromadb
import os

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
        # Always load on CPU
        model = SentenceTransformer(settings.EMBEDDING_MODEL, device='cpu')
        return model
    except Exception as e:
        logger.error(f"Error initializing embedding model: {str(e)}")
        raise

def fetch_confluence_content(confluence_url: str) -> Optional[dict]:
    """
    Fetch the main content from a Confluence page.
    Returns a dict with plain text content, display_title, and raw HTML body for richer search results.
    Uses Basic Auth with username and password for Confluence Server authentication.
    """
    try:
        import os
        from requests.auth import HTTPBasicAuth
        username = os.environ.get("CONFLUENCE_USERNAME")
        password = os.environ.get("CONFLUENCE_PASSWORD")
        if not username or not password:
            raise ValueError("Confluence username or password not set in environment variables CONFLUENCE_USERNAME and CONFLUENCE_PASSWORD.")
        response = requests.get(confluence_url, auth=HTTPBasicAuth(username, password))
        print(f"Confluence fetch status: {response.status_code}")
        print(f"Confluence fetch content (first 500 chars): {response.text[:500]}")
        response.raise_for_status()
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")
        main_content = soup.find("div", {"id": "main-content"})
        if not main_content:
            main_content = soup.body
        text_content = main_content.get_text(separator="\n", strip=True) if main_content else soup.get_text(separator="\n", strip=True)
        title_tag = soup.find("title")
        h1_tag = soup.find("h1")
        display_title = (h1_tag.get_text(strip=True) if h1_tag else (title_tag.get_text(strip=True) if title_tag else None))
        if not display_title and text_content:
            display_title = next((line for line in text_content.splitlines() if line.strip()), None)
        html_body = str(main_content) if main_content else str(soup.body)
        return {
            "content": text_content,
            "display_title": display_title,
            "html_body": html_body
        }
    except Exception as e:
        logger.error(f"Error fetching Confluence content: {str(e)}")
        return None

def add_confluence_page_to_vectordb(confluence_url: str, extra_metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """
    Fetch a Confluence page, embed its content, and store in ChromaDB.
    Also store display_title and html_body in metadata for richer search results.
    """
    try:
        page_data = fetch_confluence_content(confluence_url)
        if not page_data or not page_data.get("content"):
            raise ValueError("Failed to fetch content from Confluence URL")
        content = page_data["content"]
        display_title = page_data.get("display_title")
        html_body = page_data.get("html_body")

        client = get_vector_db_client()
        model = get_embedding_model()

        content_hash = hashlib.sha256((content or "").encode("utf-8")).hexdigest()
        collection = client.get_or_create_collection("confluence_pages")
        existing = collection.get(where={"content_hash": content_hash})
        if existing and existing.get("ids"):
            return existing["ids"][0]

        page_id = f"confluence_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        embedding = model.encode(content).tolist()
        metadata = {
            "confluence_url": confluence_url,
            "created_date": datetime.now().isoformat(),
            "content_hash": content_hash,
            "display_title": display_title,
            "html_body": html_body
        }
        if extra_metadata:
            metadata.update(extra_metadata)
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
    Search for similar Confluence pages based on a query, and return section-level match info if possible.
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

        formatted = []
        ids = results.get("ids", [])
        metadatas = results.get("metadatas", [])
        documents = results.get("documents", [])
        distances = results.get("distances", [])
        if ids and isinstance(ids[0], list):
            ids = ids[0]
        if metadatas and isinstance(metadatas[0], list):
            metadatas = metadatas[0]
        if documents and isinstance(documents[0], list):
            documents = documents[0]
        if distances and isinstance(distances[0], list):
            distances = distances[0]

        from bs4 import BeautifulSoup
        import re
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
            if similarity_score < settings.SIMILARITY_THRESHOLD:
                continue

            # SECTION MATCHING LOGIC
            section_anchor = None
            section_text = None
            best_section_score = 0
            if document:
                soup = BeautifulSoup(document, "html.parser")
                # Find all sections by heading tags (h1-h6)
                sections = []
                for heading in soup.find_all(re.compile('^h[1-6]$')):
                    # Section anchor: id or text
                    anchor = heading.get('id') or re.sub(r'[^a-zA-Z0-9]+', '-', heading.get_text().strip()).strip('-').lower()
                    # Section text: all content until next heading
                    section_content = []
                    for sib in heading.next_siblings:
                        if sib.name and re.match(r'^h[1-6]$', sib.name):
                            break
                        if hasattr(sib, 'get_text'):
                            section_content.append(sib.get_text(separator=' ', strip=True))
                        elif isinstance(sib, str):
                            section_content.append(sib.strip())
                    section_fulltext = heading.get_text(separator=' ', strip=True) + '\n' + ' '.join(section_content)
                    sections.append({
                        'anchor': anchor,
                        'text': section_fulltext
                    })
                # Find best matching section by embedding similarity
                if sections:
                    section_texts = [s['text'] for s in sections]
                    section_embeddings = model.encode(section_texts)
                    from numpy import dot
                    from numpy.linalg import norm
                    def cosine_sim(a, b):
                        return dot(a, b)/(norm(a)*norm(b))
                    best_idx = None
                    best_score = -1
                    for idx, emb in enumerate(section_embeddings):
                        score = cosine_sim(emb, query_embedding)
                        if score > best_score:
                            best_score = score
                            best_idx = idx
                    # Only add if section is reasonably relevant
                    if best_idx is not None and best_score > 0.4:
                        section_anchor = sections[best_idx]['anchor']
                        section_text = sections[best_idx]['text'][:500]
            # Add section_anchor and section_text to metadata if found
            if section_anchor:
                metadata = dict(metadata)
                metadata['section_anchor'] = section_anchor
                if section_text:
                    metadata['section_text'] = section_text
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
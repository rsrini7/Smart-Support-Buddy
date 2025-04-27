from app.services.embedding_service import get_embedding_model
from app.services.rerank_service import get_reranker
import dspy
from .bm25_utils import BM25Processor
from .retrievers import VectorRetriever, BM25Retriever
from .rag_pipeline import RAGHybridFusedRerank
from app.services.chroma_client import get_vector_db_client
from app.services.faiss_client import get_faiss_client
from app.utils.dspy_utils import get_openrouter_llm
from typing import List, Dict, Any, Optional, Callable
from app.utils.llm_augmentation import llm_summarize, llm_extract_metadata, llm_normalize_language

def load_components(db_type, db_path, embedder_model, reranker_model, llm=None):
    embedder = get_embedding_model(embedder_model)
    reranker = get_reranker(reranker_model)
    if db_type == 'chroma':
        client = get_vector_db_client(db_path)
    elif db_type == 'faiss':
        client = get_faiss_client(db_path)
    else:
        raise ValueError(f"Unknown db_type: {db_type}")
    if llm is None:
        llm = get_openrouter_llm()
    return embedder, reranker, client, llm

# --- Unified ingest utility ---
def index_vector_data(
    client,
    embedder,
    documents: List[str],
    doc_ids: List[str],
    collection_name: str,
    metadatas: Optional[List[Dict[str, Any]]] = None,
    clear_existing: bool = True,
    deduplicate: bool = True,
    llm_augment: Optional[Callable[[str], str]] = None,
    augment_metadata: bool = True,
    normalize_language: bool = True,
    target_language: str = "en"
) -> List[str]:
    collection = client.get_or_create_collection(collection_name)
    if clear_existing:
        # Chroma and FAISS both have a delete/clear method
        if hasattr(collection, 'delete'):
            existing_ids = collection.get(include=[])['ids']
            if existing_ids:
                collection.delete(ids=existing_ids)
        elif hasattr(collection, 'clear'):
            collection.clear()
    # Deduplication by content hash
    final_docs, final_ids, final_embeddings, final_metadatas = [], [], [], []
    for i, doc in enumerate(documents):
        # Normalize language
        if normalize_language:
            doc = llm_normalize_language(doc, target_language)
        # LLM-based summarization (if provided)
        if llm_augment:
            doc = llm_augment(doc)
        else:
            doc = llm_summarize(doc)
        # Compute embedding
        embedding = embedder.encode(doc).tolist()
        # Deduplication: check for content hash
        import hashlib
        content_hash = hashlib.sha256(doc.encode('utf-8')).hexdigest()
        exists = collection.get(where={"content_hash": content_hash})
        if deduplicate and exists and exists.get("ids"):
            continue
        # Augment metadata
        meta = metadatas[i] if (metadatas and i < len(metadatas)) else {}
        meta = dict(meta) if meta else {}
        meta["content_hash"] = content_hash
        if augment_metadata:
            extracted = llm_extract_metadata(doc)
            meta.update({k: v for k, v in extracted.items() if k not in meta})
        final_docs.append(doc)
        final_ids.append(doc_ids[i])
        final_embeddings.append(embedding)
        final_metadatas.append(meta)
    if final_docs:
        collection.add(
            ids=final_ids,
            embeddings=final_embeddings,
            metadatas=final_metadatas,
            documents=final_docs,
        )
    return final_ids

def create_bm25_index(documents):
    if not documents:
        # Return a dummy retriever that always returns an empty list
        class EmptyBM25Processor:
            def get_scores(self, query):
                return []
        return EmptyBM25Processor()
    return BM25Processor(documents)

def create_retrievers(collection, embedder, bm25_processor, corpus, doc_ids: Optional[List[str]] = None, metadatas: Optional[List[Dict[str, Any]]] = None, k_embed=5, k_bm25=5):
    """Creates vector and BM25 retrievers, passing IDs and metadata to BM25Retriever."""
    vector_retriever = VectorRetriever(collection, embedder, k=k_embed)
    # Pass doc_ids and metadatas to BM25Retriever
    bm25_retriever = BM25Retriever(bm25_processor, corpus, doc_ids=doc_ids, metadatas=metadatas, k=k_bm25)
    return vector_retriever, bm25_retriever

def create_rag_pipeline(vector_retriever, keyword_retriever, reranker_model, llm, k_rerank=3):
    return RAGHybridFusedRerank(
        vector_retriever=vector_retriever,
        keyword_retriever=keyword_retriever,
        reranker_model=reranker_model,
        llm=llm,
        rerank_k=k_rerank
    )
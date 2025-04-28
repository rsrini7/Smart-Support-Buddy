import dspy

class VectorRetriever(dspy.Retrieve):
    """DSPy Retriever for either ChromaDB or FAISS collections using SentenceTransformer embeddings."""
    def __init__(self, collection, embed_model, k=3):
        self._collection = collection
        self._embedder = embed_model
        self._k = k
        super().__init__(k=k)

    def forward(self, query, k=None):
        k = k or self._k
        query_emb = self._embedder.encode([query], show_progress_bar=False).tolist()
        # Only include valid Chroma/FAISS fields
        results = self._collection.query(query_embeddings=query_emb, n_results=k, include=['documents', 'metadatas'])

        # Ensure results are not None and contain expected keys
        if not results or not results.get('documents') or not results['documents'][0]:
            return [] # Return empty list if no results or malformed

        # Construct dspy.Example with document text and metadata (including the ID if available)
        docs = []
        docs_ids = results.get('ids', [None])[0] if 'ids' in results and results['ids'] else [str(i) for i in range(len(results['documents'][0]))]
        for i, doc_text in enumerate(results['documents'][0]):
            metadata = results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] and i < len(results['metadatas'][0]) else {}
            doc_id = docs_ids[i] if docs_ids and i < len(docs_ids) else None
            # Add the document ID to the metadata if it's not already there
            if doc_id and 'id' not in metadata:
                metadata['id'] = doc_id
            docs.append(dspy.Example(long_text=doc_text, **metadata)) # Pass metadata as keyword arguments
        return docs

from typing import List, Dict, Any, Optional

class BM25Retriever(dspy.Retrieve):
    """DSPy Retriever using BM25Processor for keyword search."""
    def __init__(self, bm25_processor, corpus, doc_ids: Optional[List[str]] = None, metadatas: Optional[List[Dict[str, Any]]] = None, k=3):
        self._bm25_processor = bm25_processor
        self._corpus = corpus
        # Store IDs and Metadatas if provided
        self._doc_ids = doc_ids if doc_ids else [None] * len(corpus)
        self._metadatas = metadatas if metadatas else [{}] * len(corpus)
        # Ensure lists have the same length as corpus for safe indexing
        if len(self._doc_ids) != len(corpus) or len(self._metadatas) != len(corpus):
            # Log a warning or raise an error, here we'll pad for safety, but ideally lengths should match
            print(f"Warning: BM25Retriever received mismatched lengths for corpus ({len(corpus)}), ids ({len(doc_ids or [])}), and metadatas ({len(metadatas or [])}). Padding...")
            self._doc_ids = (doc_ids or []) + [None] * (len(corpus) - len(doc_ids or []))
            self._metadatas = (metadatas or []) + [{}] * (len(corpus) - len(metadatas or []))

        self._k = k
        super().__init__(k=k)

    def forward(self, query, k=None):
        k = k or self._k
        scores = self._bm25_processor.get_scores(query)
        # Ensure all scores are floats (handle str/float mix)
        scores = [float(s) if not isinstance(s, float) else s for s in scores]
        # Get indices and scores, sorted by score
        ranked_indices_scores = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)

        docs = []
        for i, score in ranked_indices_scores:
            if score <= 0 or len(docs) >= k:
                break # Stop if score is non-positive or we have enough docs
            # Get the original document text, ID, and metadata using the index 'i'
            doc_text = self._corpus[i]
            doc_id = self._doc_ids[i]
            metadata = self._metadatas[i].copy() # Use a copy to avoid modifying the original
            # Ensure the ID is in the metadata for consistency
            if doc_id and 'id' not in metadata:
                metadata['id'] = doc_id
            # Add BM25 score to metadata if desired
            metadata['bm25_score'] = score
            docs.append(dspy.Example(long_text=doc_text, **metadata))

        return docs
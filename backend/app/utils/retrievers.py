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
        results = self._collection.query(query_embeddings=query_emb, n_results=k, include=['documents'])
        # Both Chroma and FAISS return documents in the same format
        docs = [dspy.Example(long_text=doc) for doc in results['documents'][0]]
        return docs

class BM25Retriever(dspy.Retrieve):
    """DSPy Retriever using BM25Processor for keyword search."""
    def __init__(self, bm25_processor, corpus, k=3):
        self._bm25_processor = bm25_processor
        self._corpus = corpus
        self._k = k
        super().__init__(k=k)

    def forward(self, query, k=None):
        k = k or self._k
        scores = self._bm25_processor.get_scores(query)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:k]
        docs = [dspy.Example(long_text=self._corpus[i]) for i, score in ranked if score > 0]
        return docs
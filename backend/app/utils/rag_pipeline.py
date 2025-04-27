import dspy

class RAGHybridFusedRerank(dspy.Module):
    """
    DSPy Module implementing a RAG pipeline with:
    1. Hybrid Retrieval (Vector + BM25)
    2. Fusion (Combine + Deduplicate)
    3. Neural Reranking (CrossEncoder)
    4. LLM Generation
    """
    def __init__(self, vector_retriever, keyword_retriever, reranker_model, llm, rerank_k=3):
        super().__init__()
        self.vector_retrieve = vector_retriever
        self.keyword_retrieve = keyword_retriever
        self.reranker = reranker_model
        self.generate = dspy.Predict("context, question -> answer")
        self.llm = llm
        self.rerank_k = rerank_k

    def rerank(self, query, documents_with_meta):
        """Reranks documents based on query, preserving metadata."""
        # Extract text for reranking, keep original object
        texts_to_rank = [doc['long_text'] for doc in documents_with_meta]
        scores = self.reranker.predict([(query, text) for text in texts_to_rank])
        # Combine original objects with scores and sort
        ranked = sorted(zip(documents_with_meta, scores), key=lambda x: x[1], reverse=True)
        # Return the top K original objects
        return [doc for doc, _ in ranked[:self.rerank_k]]

    def forward(self, question, use_llm=True):
        vector_results = self.vector_retrieve(question) # List of dspy.Example
        keyword_results = self.keyword_retrieve(question) # List of dspy.Example

        # Fuse based on a unique identifier if available (e.g., 'id'), otherwise fallback to text
        # Assuming retrievers return dspy.Example objects with an 'id' field
        fused_docs_map = {}
        for doc in vector_results + keyword_results:
            doc_id = doc.get('id', doc.get('long_text')) # Use ID if present, else text
            if doc_id not in fused_docs_map:
                fused_docs_map[doc_id] = doc

        fused_list = list(fused_docs_map.values()) # List of unique dspy.Example

        # Rerank based on text, but return the full dspy.Example objects
        reranked_examples = self.rerank(question, fused_list)

        # Prepare context string for LLM generation
        context_text = "\n".join([ex.long_text for ex in reranked_examples])

        if not use_llm:
            # Return the reranked dspy.Example objects directly
            return type('RAGResult', (), {'context': reranked_examples, 'answer': None})()

        with dspy.settings.context(lm=self.llm):
            prediction = self.generate(question=question, context=context_text)
            # Attach the full reranked examples (with metadata) to the prediction
            prediction.context = reranked_examples
            return prediction
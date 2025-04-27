from typing import List
from rank_bm25 import BM25Okapi
import nltk
import os
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

def ensure_nltk_resources():
    """Ensure required NLTK resources are downloaded."""
    # Get absolute path to .venv/nltk_data relative to this file
    nltk_data_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', '..', '.venv', 'nltk_data')
    )
    if not os.path.exists(nltk_data_dir):
        os.makedirs(nltk_data_dir, exist_ok=True)
    if nltk_data_dir not in nltk.data.path:
        nltk.data.path.insert(0, nltk_data_dir)
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        nltk.download('punkt', download_dir=nltk_data_dir)
        nltk.download('punkt_tab', download_dir=nltk_data_dir)
        nltk.download('stopwords', download_dir=nltk_data_dir)

class BM25Processor:
    def __init__(self, documents: List[str]):
        ensure_nltk_resources()
        stop_words = set(stopwords.words('english'))
        self.tokenized_docs = [
            [word.lower() for word in word_tokenize(doc) if word.isalnum() and word.lower() not in stop_words]
            for doc in documents
        ]
        self.bm25 = BM25Okapi(self.tokenized_docs)
        self.documents = documents

    def get_scores(self, query: str) -> List[float]:
        ensure_nltk_resources()
        stop_words = set(stopwords.words('english'))
        tokenized_query = [
            word.lower() for word in word_tokenize(query)
            if word.isalnum() and word.lower() not in stop_words
        ]
        return self.bm25.get_scores(tokenized_query)
import hashlib

def compute_content_hash(*fields: str) -> str:
    """
    Compute a SHA256 hash from concatenated fields for deduplication.
    """
    dedup_str = ''.join(fields)
    return hashlib.sha256(dedup_str.encode("utf-8")).hexdigest()

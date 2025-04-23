import faiss
import numpy as np
import os
import logging
import pickle
from typing import List, Tuple, Optional, Dict, Any
from app.core.config import settings
from app.services.embedding_service import get_embedding_model

logger = logging.getLogger(__name__)

class FaissCollection:
    """ Represents a single collection within the FAISS client. """
    def __init__(self, name: str, index_path: str, metadata_path: str, dimension: int):
        self.name = name
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.dimension = dimension
        self.index = None
        self.metadata_store: Dict[str, Dict[str, Any]] = {}
        self.doc_store: Dict[str, str] = {}
        self.faiss_id_to_doc_id: Dict[int, str] = {}
        self.doc_id_to_faiss_id: Dict[str, int] = {}
        self.next_internal_id: int = 0
        self._load()

    def _load(self):
        """ Load index and metadata from disk. """
        loaded_index = False
        if os.path.exists(self.index_path):
            try:
                self.index = faiss.read_index(self.index_path)
                if not isinstance(self.index, faiss.IndexIDMap):
                     logger.warning(f"Loaded index for {self.name} is not IndexIDMap. Re-initializing.")
                     self.index = None # Force reinitialization
                elif self.index.d != self.dimension:
                    logger.warning(f"Index dimension mismatch for {self.name} (loaded {self.index.d}, expected {self.dimension}). Re-initializing.")
                    self.index = None # Force reinitialization
                else:
                    logger.info(f"Loaded FAISS index for collection '{self.name}' from {self.index_path} ({self.index.ntotal} vectors)")
                    loaded_index = True
            except Exception as e:
                logger.error(f"Error loading FAISS index for {self.name} from {self.index_path}: {e}. Re-initializing.")
                self.index = None

        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, 'rb') as f:
                    saved_data = pickle.load(f)
                    self.metadata_store = saved_data.get('metadata', {})
                    self.doc_store = saved_data.get('documents', {})
                    self.faiss_id_to_doc_id = saved_data.get('faiss_map', {})
                    self.doc_id_to_faiss_id = {v: k for k, v in self.faiss_id_to_doc_id.items()} # Rebuild reverse map
                    self.next_internal_id = saved_data.get('next_id', 0)
                logger.info(f"Loaded metadata for collection '{self.name}' from {self.metadata_path}. Next ID: {self.next_internal_id}")
                # If index loading failed but metadata loaded, reset metadata
                if not loaded_index:
                     logger.warning(f"Index loading failed for {self.name}, resetting metadata.")
                     self._reset_stores()

            except Exception as e:
                logger.error(f"Error loading metadata for {self.name} from {self.metadata_path}: {e}. Resetting metadata.")
                self._reset_stores()
                if loaded_index:
                     logger.warning("Metadata loading failed but index loaded. Index will be reset.")
                     self.index = None # Reset index too if metadata failed

        if self.index is None:
            logger.info(f"Creating new FAISS index (IndexFlatL2 + IndexIDMap) for collection '{self.name}' with dimension {self.dimension}.")
            base_index = faiss.IndexFlatL2(self.dimension)
            self.index = faiss.IndexIDMap(base_index)
            self._reset_stores()

    def _reset_stores(self):
        self.metadata_store = {}
        self.doc_store = {}
        self.faiss_id_to_doc_id = {}
        self.doc_id_to_faiss_id = {}
        self.next_internal_id = 0

    def _save(self):
        """ Save index and metadata to disk. """
        if self.index is None:
            logger.warning(f"Attempted to save FAISS index for {self.name}, but it's not initialized.")
            return
        try:
            logger.info(f"Saving FAISS index for {self.name} to {self.index_path} ({self.index.ntotal} vectors)")
            faiss.write_index(self.index, self.index_path)
            logger.info(f"Saving metadata for {self.name} to {self.metadata_path}")
            with open(self.metadata_path, 'wb') as f:
                pickle.dump({
                    'metadata': self.metadata_store,
                    'documents': self.doc_store,
                    'faiss_map': self.faiss_id_to_doc_id,
                    'next_id': self.next_internal_id
                }, f)
            logger.info(f"FAISS index and metadata for {self.name} saved successfully.")
        except Exception as e:
            logger.error(f"Error saving FAISS index or metadata for {self.name}: {e}")

    def add(self, ids: List[str], embeddings: List[List[float]], metadatas: Optional[List[Dict]] = None, documents: Optional[List[str]] = None):
        if not ids or not embeddings:
            logger.warning(f"[{self.name}] Add called with empty ids or embeddings.")
            return

        if len(ids) != len(embeddings):
            raise ValueError(f"[{self.name}] Number of ids ({len(ids)}) and embeddings ({len(embeddings)}) must match.")
        if metadatas and len(ids) != len(metadatas):
            raise ValueError(f"[{self.name}] Number of ids ({len(ids)}) and metadatas ({len(metadatas)}) must match.")
        if documents and len(ids) != len(documents):
            raise ValueError(f"[{self.name}] Number of ids ({len(ids)}) and documents ({len(documents)}) must match.")

        embeddings_np = np.array(embeddings).astype('float32')
        if embeddings_np.shape[1] != self.dimension:
            raise ValueError(f"[{self.name}] Embedding dimension mismatch: expected {self.dimension}, got {embeddings_np.shape[1]}")

        faiss_ids_to_add = []
        embeddings_to_add = []
        added_doc_ids = []

        for i, doc_id in enumerate(ids):
            if doc_id in self.doc_id_to_faiss_id:
                logger.debug(f"[{self.name}] ID '{doc_id}' already exists. Skipping add.")
                # TODO: Implement update logic if needed?
                continue

            internal_id = self.next_internal_id
            faiss_ids_to_add.append(internal_id)
            embeddings_to_add.append(embeddings_np[i])

            self.doc_id_to_faiss_id[doc_id] = internal_id
            self.faiss_id_to_doc_id[internal_id] = doc_id
            if metadatas:
                self.metadata_store[doc_id] = metadatas[i]
            if documents:
                self.doc_store[doc_id] = documents[i]

            added_doc_ids.append(doc_id)
            self.next_internal_id += 1

        if embeddings_to_add:
            embeddings_to_add_np = np.array(embeddings_to_add).astype('float32')
            faiss_ids_to_add_np = np.array(faiss_ids_to_add).astype('int64')
            try:
                self.index.add_with_ids(embeddings_to_add_np, faiss_ids_to_add_np)
                logger.info(f"[{self.name}] Added {len(added_doc_ids)} new items. Index size: {self.index.ntotal}")
                self._save()
            except Exception as e:
                logger.error(f"[{self.name}] Error adding embeddings to FAISS index: {e}")
                # Rollback metadata/doc changes for failed adds
                for doc_id in added_doc_ids:
                    internal_id = self.doc_id_to_faiss_id.pop(doc_id, None)
                    if internal_id is not None:
                        self.faiss_id_to_doc_id.pop(internal_id, None)
                    self.metadata_store.pop(doc_id, None)
                    self.doc_store.pop(doc_id, None)
                # Note: Rolling back next_internal_id is tricky if partial success occurred
                raise # Re-raise the exception

    def query(self, query_embeddings: List[List[float]], n_results: int = 10, include: List[str] = ['metadatas', 'documents', 'distances'], where: Optional[Dict] = None, where_document: Optional[Dict] = None) -> Dict[str, List[Any]]:
        """ Query the collection. Mimics ChromaDB's return format. """
        if self.index is None or self.index.ntotal == 0:
            logger.warning(f"[{self.name}] Query called on empty or uninitialized index.")
            # Return format consistent with ChromaDB for empty results
            return {'ids': [], 'distances': [], 'metadatas': [], 'documents': [], 'embeddings': []}

        if not query_embeddings:
             return {'ids': [], 'distances': [], 'metadatas': [], 'documents': [], 'embeddings': []}

        # Currently, FAISS client doesn't support 'where' or 'where_document' filters during search.
        # This would require iterating through all results and filtering afterwards, which is inefficient.
        # For now, we log a warning if these filters are used.
        if where or where_document:
            logger.warning(f"[{self.name}] FAISS client currently does not support 'where' or 'where_document' filters during query. Filters ignored.")

        query_embeddings_np = np.array(query_embeddings).astype('float32')
        if query_embeddings_np.shape[1] != self.dimension:
            raise ValueError(f"[{self.name}] Query embedding dimension mismatch: expected {self.dimension}, got {query_embeddings_np.shape[1]}")

        # FAISS search expects a single batch of queries
        # We only process the first query embedding if multiple are provided, mimicking Chroma's typical single-query behavior
        if query_embeddings_np.shape[0] > 1:
            logger.warning(f"[{self.name}] Multiple query embeddings provided ({query_embeddings_np.shape[0]}), but FAISS client currently processes only the first one.")
            query_embeddings_np = query_embeddings_np[0:1]

        k = min(n_results, self.index.ntotal)
        if k <= 0:
            return {'ids': [], 'distances': [], 'metadatas': [], 'documents': [], 'embeddings': []}

        # FAISS search returns distances (L2 squared) and internal IDs
        all_distances, all_internal_ids = self.index.search(query_embeddings_np, k)

        # Results for the first (and only processed) query
        internal_ids_list = all_internal_ids[0]
        distances_list = all_distances[0]

        final_ids = []
        final_distances = []
        final_metadatas = []
        final_documents = []

        for j, internal_id in enumerate(internal_ids_list):
            if internal_id == -1: # FAISS uses -1 if fewer than k results found
                continue

            doc_id = self.faiss_id_to_doc_id.get(int(internal_id)) # Ensure internal_id is int
            if doc_id:
                final_ids.append(doc_id)
                if 'distances' in include:
                    # FAISS returns L2 squared, Chroma often uses cosine similarity or L2.
                    # We'll return L2 distance.
                    final_distances.append(float(np.sqrt(distances_list[j]))) # Ensure float
                if 'metadatas' in include:
                    final_metadatas.append(self.metadata_store.get(doc_id, {}))
                if 'documents' in include:
                    final_documents.append(self.doc_store.get(doc_id, ""))
                # 'embeddings' are typically not returned by FAISS search directly

        # Construct the final result dictionary in ChromaDB format
        final_results = {
            'ids': [final_ids], # Wrap in a list to match Chroma's structure for single query
            'distances': [final_distances] if 'distances' in include else None,
            'metadatas': [final_metadatas] if 'metadatas' in include else None,
            'documents': [final_documents] if 'documents' in include else None,
            'embeddings': None # Embeddings not retrieved in standard search
        }

        # Remove keys if not requested (as per ChromaDB behavior)
        for key in list(final_results.keys()):
             if final_results[key] is None:
                 del final_results[key]

        return final_results

    def _matches_where(self, metadata: Optional[Dict[str, Any]], where_clause: Dict[str, Any]) -> bool:
        """ Check if an item's metadata matches the where clause. """
        if not metadata:
            return False
        for key, value in where_clause.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True

    def _matches_where_document(self, document: Optional[str], where_document_clause: Dict[str, Any]) -> bool:
        """ Check if an item's document content matches the where_document clause. """
        if not document:
            return False
        if '$contains' in where_document_clause:
            search_term = where_document_clause['$contains']
            return search_term in document
        # Add more complex document filtering logic here if needed
        logger.warning(f"[{self.name}] Unsupported where_document filter: {where_document_clause}")
        return False

    def get(self, ids: Optional[List[str]] = None, where: Optional[Dict[str, Any]] = None, limit: Optional[int] = None, offset: Optional[int] = None, where_document: Optional[Dict[str, Any]] = None, include: List[str] = ['metadatas', 'documents']) -> Dict[str, List[Any]]:
        """ Mimics ChromaDB's get method, including basic 'where' and 'where_document' filtering. """
        # Remove the warning log as filtering is implemented
        # logger.warning(f"[{self.name}] FAISS get method currently only supports filtering by ID. 'where' and 'where_document' clauses are ignored.")

        potential_ids = ids if ids else list(self.doc_id_to_faiss_id.keys())

        filtered_items = []
        for doc_id in potential_ids:
            if doc_id not in self.doc_id_to_faiss_id:
                continue # Skip if ID doesn't exist in this collection

            metadata = self.metadata_store.get(doc_id)
            document = self.doc_store.get(doc_id)

            # Apply 'where' filter (metadata)
            if where and not self._matches_where(metadata, where):
                continue

            # Apply 'where_document' filter (document content)
            if where_document and not self._matches_where_document(document, where_document):
                continue

            # If all filters pass, add the item
            item = {'id': doc_id}
            if 'metadatas' in include: item['metadata'] = metadata
            if 'documents' in include: item['document'] = document
            # Note: Embeddings are not typically stored/retrieved in 'get'
            filtered_items.append(item)

        # Apply limit and offset *after* filtering
        start = offset if offset else 0
        end = (start + limit) if limit is not None else len(filtered_items)
        paginated_items = filtered_items[start:end]

        # Construct final results dictionary
        final_results = {'ids': [item['id'] for item in paginated_items]}
        if 'metadatas' in include:
            final_results['metadatas'] = [item.get('metadata') for item in paginated_items]
        if 'documents' in include:
            final_results['documents'] = [item.get('document') for item in paginated_items]

        return final_results

    def delete(self, ids: Optional[List[str]] = None, where: Optional[Dict[str, Any]] = None, where_document: Optional[Dict[str, Any]] = None) -> List[str]:
        """ Mimics ChromaDB's delete method. Filtering is basic (only by ID). """
        if where or where_document:
            logger.warning(f"[{self.name}] FAISS delete method currently only supports filtering by ID. 'where' and 'where_document' clauses are ignored.")

        if not ids:
             logger.warning(f"[{self.name}] Delete called without specific IDs. This is currently not supported for safety. Provide IDs to delete.")
             return []

        faiss_ids_to_remove = []
        deleted_doc_ids = []

        for doc_id in ids:
            internal_id = self.doc_id_to_faiss_id.pop(doc_id, None)
            if internal_id is not None:
                faiss_ids_to_remove.append(internal_id)
                self.faiss_id_to_doc_id.pop(internal_id, None)
                self.metadata_store.pop(doc_id, None)
                self.doc_store.pop(doc_id, None)
                deleted_doc_ids.append(doc_id)
            else:
                logger.warning(f"[{self.name}] ID '{doc_id}' not found for deletion.")

        if faiss_ids_to_remove:
            try:
                remove_result = self.index.remove_ids(np.array(faiss_ids_to_remove).astype('int64'))
                logger.info(f"[{self.name}] Removed {remove_result} items from FAISS index. Attempted: {len(faiss_ids_to_remove)}. Index size: {self.index.ntotal}")
                if remove_result != len(faiss_ids_to_remove):
                     logger.warning(f"[{self.name}] Discrepancy in removed count from FAISS index.")
                self._save()
            except Exception as e:
                logger.error(f"[{self.name}] Error removing IDs from FAISS index: {e}")
                # Note: Metadata/doc store changes are already done. Rollback is complex.
                # Re-raise or handle as appropriate.
                # For now, return the IDs we *thought* we deleted.

        return deleted_doc_ids

    def count(self) -> int:
        """ Returns the number of items in the collection. """
        return self.index.ntotal if self.index else 0


class FaissClient:
    """ Manages multiple FAISS collections. """
    def __init__(self, base_path: str):
        self.base_path = base_path
        self.collections: Dict[str, FaissCollection] = {}
        self.dimension = self._get_embedding_dimension()
        os.makedirs(self.base_path, exist_ok=True)
        logger.info(f"FAISS Client initialized. Base path: {self.base_path}, Dimension: {self.dimension}")

    def _get_embedding_dimension(self) -> int:
        try:
            model = get_embedding_model()
            dummy_embedding = model.encode("test")
            dimension = len(dummy_embedding)
            logger.info(f"Detected embedding dimension: {dimension}")
            return dimension
        except Exception as e:
            logger.error(f"Could not determine embedding dimension: {e}")
            dimension = 768 # Fallback to a common default
            logger.warning(f"Falling back to default dimension: {dimension}")
            return dimension

    def get_or_create_collection(self, name: str) -> FaissCollection:
        if name in self.collections:
            return self.collections[name]
        else:
            logger.info(f"Creating new FAISS collection: {name}")
            collection_path = os.path.join(self.base_path, name)
            os.makedirs(collection_path, exist_ok=True)
            index_path = os.path.join(collection_path, "index.faiss")
            metadata_path = os.path.join(collection_path, "metadata.pkl")
            collection = FaissCollection(name, index_path, metadata_path, self.dimension)
            self.collections[name] = collection
            return collection

    def get_collection(self, name: str) -> Optional[FaissCollection]:
        # Try in-memory first
        if name in self.collections:
            return self.collections[name]
        # Try loading from disk if folder exists
        collection_path = os.path.join(self.base_path, name)
        index_path = os.path.join(collection_path, "index.faiss")
        metadata_path = os.path.join(collection_path, "metadata.pkl")
        if os.path.exists(collection_path) and (os.path.exists(index_path) or os.path.exists(metadata_path)):
            collection = FaissCollection(name, index_path, metadata_path, self.dimension)
            self.collections[name] = collection
            return collection
        return None

    def delete_collection(self, name: str):
        if name in self.collections:
            collection = self.collections.pop(name)
            collection_path = os.path.join(self.base_path, name)
            try:
                # Attempt to remove files and directory
                if os.path.exists(collection.index_path):
                    os.remove(collection.index_path)
                if os.path.exists(collection.metadata_path):
                    os.remove(collection.metadata_path)
                if os.path.exists(collection_path):
                     # Check if dir is empty before removing, might fail otherwise
                     if not os.listdir(collection_path):
                          os.rmdir(collection_path)
                     else:
                          logger.warning(f"Directory {collection_path} not empty after removing index/metadata files.")
                logger.info(f"Deleted FAISS collection '{name}' and associated files.")
            except Exception as e:
                logger.error(f"Error deleting files for collection {name}: {e}")
        else:
            logger.warning(f"Attempted to delete non-existent FAISS collection: {name}")

    def list_collections(self) -> List[Dict[str, Any]]:
        """
        Mimic Chroma's list_collections format.
        Scan the base_path directory for all subdirectories that contain FAISS index or metadata files.
        Return their names as collections, even if not loaded in memory, and include record count.
        """
        collections = set(self.collections.keys())
        # Scan for additional collections on disk
        if os.path.exists(self.base_path):
            for entry in os.listdir(self.base_path):
                entry_path = os.path.join(self.base_path, entry)
                if os.path.isdir(entry_path):
                    has_metadata = os.path.exists(os.path.join(entry_path, "metadata.pkl"))
                    has_index = any(f.endswith(".index") for f in os.listdir(entry_path)) if os.path.exists(entry_path) else False
                    if has_metadata or has_index:
                        collections.add(entry)
        result = []
        for name in sorted(collections):
            try:
                collection = self.get_collection(name)
                count = collection.count() if collection else 0
            except Exception:
                count = 0
            result.append({"name": name, "record_count": count})
        return result

    def get_collections_with_records(self) -> List[Dict[str, Any]]:
        """
        Returns all collections and their records (id, document, metadata) in Chroma-like format.
        """
        results = []
        for col in self.list_collections() or []:
            collection = self.get_collection(col["name"])
            if collection:
                all_ids = list(collection.doc_store.keys())
                records = []
                for doc_id in all_ids:
                    record = {
                        "id": doc_id,
                        "document": collection.doc_store.get(doc_id, ""),
                        "metadata": collection.metadata_store.get(doc_id, {})
                    }
                    records.append(record)
                results.append({
                    "collection_name": col["name"],
                    "records": records
                })
            else:
                results.append({
                    "collection_name": col["name"],
                    "records": []
                })
        return results

# Global instance (optional, depends on usage pattern)
# _global_faiss_client = None

# def get_faiss_client(base_path: str = None) -> FaissClient:
#     global _global_faiss_client
#     if _global_faiss_client is None:
#         path = base_path or settings.FAISS_INDEX_PATH
#         _global_faiss_client = FaissClient(path)
#     # Ensure base path matches if called again?
#     # elif base_path and _global_faiss_client.base_path != base_path:
#     #     logger.warning("Requesting FAISS client with different base path. Returning existing instance.")
#     return _global_faiss_client
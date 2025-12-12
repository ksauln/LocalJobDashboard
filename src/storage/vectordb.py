import chromadb
from chromadb.config import Settings
from typing import Any, Dict, List, Optional


def get_chroma_client(persist_dir: str):
    return chromadb.PersistentClient(path=persist_dir, settings=Settings(allow_reset=True, anonymized_telemetry=False))


def get_or_create_collection(client, name: str):
    return client.get_or_create_collection(name=name)


def add_documents(collection, ids: List[str], documents: List[str], metadatas: List[Dict[str, Any]], embeddings: List[List[float]]):
    collection.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)


def query(collection, query_embedding: List[float], n_results: int, where_filter: Optional[Dict[str, Any]] = None):
    return collection.query(query_embeddings=[query_embedding], n_results=n_results, where=where_filter)


def get(collection, where_filter: Optional[Dict[str, Any]] = None, limit: Optional[int] = None):
    return collection.get(where=where_filter, limit=limit)


def clear_collection(collection) -> None:
    """Remove all documents from a collection."""
    try:
        collection.delete(where={})
    except Exception:
        # Fallback: delete by ids if where={} not supported
        existing = collection.get()
        ids = existing.get("ids", [])
        if ids:
            collection.delete(ids=ids)

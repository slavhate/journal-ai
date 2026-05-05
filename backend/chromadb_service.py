import chromadb
import os
from backend.config import CHROMADB_PATH


_client = None
_collection = None


def get_client():
    global _client
    if _client is None:
        os.makedirs(CHROMADB_PATH, exist_ok=True)
        _client = chromadb.PersistentClient(path=CHROMADB_PATH)
    return _client


def get_collection():
    global _collection
    if _collection is None:
        client = get_client()
        _collection = client.get_or_create_collection(
            name="daily_entries",
            metadata={"hnsw:space": "cosine"}
        )
    return _collection


def upsert_document(date: str, content: str, embedding: list[float], categories: list[str]):
    collection = get_collection()
    collection.upsert(
        ids=[date],
        documents=[content],
        embeddings=[embedding],
        metadatas=[{"date": date, "categories": ",".join(categories)}]
    )


def query_documents(query_embedding: list[float], n_results: int = 5) -> dict:
    collection = get_collection()
    count = collection.count()
    actual_n = min(n_results, count)
    if actual_n == 0:
        return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
    return collection.query(
        query_embeddings=[query_embedding],
        n_results=actual_n,
        include=["documents", "metadatas", "distances"]
    )

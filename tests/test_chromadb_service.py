import pytest

from backend.chromadb_service import get_collection, upsert_document, query_documents


def test_get_collection_returns_collection():
    collection = get_collection()
    assert collection.name == "daily_entries"


def test_upsert_and_query_document():
    embedding = [0.1] * 384
    upsert_document(
        date="2026-05-05",
        content="Work standup meeting about project alpha",
        embedding=embedding,
        categories=["work"]
    )
    results = query_documents(
        query_embedding=embedding,
        n_results=1
    )
    assert len(results["ids"][0]) == 1
    assert results["ids"][0][0] == "2026-05-05"

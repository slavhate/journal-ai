import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient


from backend.main import app


@pytest.fixture(autouse=True)
def mock_ollama():
    format_response = {"markdown": "### Note\n- Test entry", "events": []}
    embedding_response = [0.1] * 384
    with patch("backend.routers.entries.format_entry", new_callable=AsyncMock, return_value=format_response):
        with patch("backend.routers.entries.generate_embedding", new_callable=AsyncMock, return_value=embedding_response):
            with patch("backend.routers.entries.upsert_document"):
                yield


def test_create_entry():
    with TestClient(app) as client:
        response = client.post("/api/entries", json={
            "category": "work",
            "raw_text": "Had standup meeting"
        })
    assert response.status_code == 200
    data = response.json()
    assert data["id"] > 0
    assert data["category"] == "work"


def test_get_entries_by_date():
    with TestClient(app) as client:
        client.post("/api/entries", json={
            "category": "personal",
            "raw_text": "Morning run"
        })
        from datetime import date
        today = date.today().isoformat()
        response = client.get(f"/api/entries/{today}")
    assert response.status_code == 200
    data = response.json()
    assert "personal" in data


def test_delete_entry():
    with TestClient(app) as client:
        resp = client.post("/api/entries", json={
            "category": "finance",
            "raw_text": "Paid rent"
        })
        entry_id = resp.json()["id"]
        del_resp = client.delete(f"/api/entries/{entry_id}")
    assert del_resp.status_code == 200

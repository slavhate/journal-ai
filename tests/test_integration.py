import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient


from backend.main import app


@pytest.fixture(autouse=True)
def mock_ollama_services():
    format_response = {
        "markdown": "### Meeting\n- Discussed project timeline",
        "events": [{"date": "2026-05-10", "type": "todo", "title": "Submit report"}]
    }
    embedding = [0.1] * 384

    with patch("backend.routers.entries.format_entry", new_callable=AsyncMock, return_value=format_response):
        with patch("backend.routers.entries.generate_embedding", new_callable=AsyncMock, return_value=embedding):
            with patch("backend.routers.entries.upsert_document"):
                yield


def test_full_entry_lifecycle():
    with TestClient(app) as client:
        resp = client.post("/api/entries", json={
            "category": "work",
            "raw_text": "Had project meeting, need to submit report by May 10"
        })
        assert resp.status_code == 200
        entry_id = resp.json()["id"]

        from datetime import date
        today = date.today().isoformat()
        resp = client.get(f"/api/entries/{today}")
        assert resp.status_code == 200
        assert len(resp.json()["work"]) >= 1

        resp = client.get("/api/today")
        assert resp.status_code == 200

        resp = client.put(f"/api/entries/{entry_id}", json={"raw_text": "Updated: project meeting went well"})
        assert resp.status_code == 200

        resp = client.delete(f"/api/entries/{entry_id}")
        assert resp.status_code == 200

        resp = client.get("/api/days")
        assert resp.status_code == 200


def test_static_frontend_served():
    with TestClient(app) as client:
        resp = client.get("/")
    assert resp.status_code == 200
    assert "Daily Journal" in resp.text

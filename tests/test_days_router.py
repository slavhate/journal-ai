import pytest
from fastapi.testclient import TestClient


from backend.main import app
from backend.database import init_db, create_event
from backend.markdown_service import write_md_file


def setup_module(module):
    init_db()
    write_md_file("2026-05-05", "# 2026-05-05\n\n## Work\n### Standup\n- Discussed timeline\n")


def test_get_days_list():
    with TestClient(app) as client:
        response = client.get("/api/days")
    assert response.status_code == 200
    data = response.json()
    assert "2026-05-05" in data


def test_get_day_content():
    with TestClient(app) as client:
        response = client.get("/api/days/2026-05-05")
    assert response.status_code == 200
    data = response.json()
    assert "content" in data
    assert "Standup" in data["content"]


def test_get_today_events():
    from datetime import date
    today = date.today().isoformat()
    create_event(today, "todo", "Submit report", "2026-05-04")
    with TestClient(app) as client:
        response = client.get("/api/today")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[-1]["title"] == "Submit report"

# Journal AI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a containerized daily journaling app with AI-powered entry formatting, event extraction, and semantic search via Open WebUI.

**Architecture:** Single FastAPI monolith serves a vanilla HTML/JS/CSS frontend and manages all data (SQLite, ChromaDB, MD files). Ollama runs as a sibling container for LLM inference. Open WebUI tool script queries ChromaDB for semantic search.

**Tech Stack:** Python 3.11, FastAPI, SQLite, ChromaDB, Ollama (llama3.2:3b + nomic-embed-text), Docker Compose, vanilla HTML/JS/CSS.

---

## File Structure

```
journal-ai/
├── backend/
│   ├── main.py              — FastAPI app, mounts static files, includes routers
│   ├── config.py            — Settings from env vars (Ollama URL, data dir, models)
│   ├── database.py          — SQLite connection, table creation, CRUD operations
│   ├── ollama_service.py    — Ollama API client (formatting + embedding calls)
│   ├── markdown_service.py  — MD file read/write/rebuild logic
│   ├── chromadb_service.py  — ChromaDB collection management, embed/query
│   ├── routers/
│   │   ├── entries.py       — POST/PUT/DELETE/GET /api/entries endpoints
│   │   ├── days.py          — GET /api/days, /api/days/{date} endpoints
│   │   └── today.py         — GET /api/today endpoint
│   ├── requirements.txt     — Python dependencies
│   └── Dockerfile           — Python 3.11-slim image
├── frontend/
│   ├── index.html           — Main page layout (header, main column, sidebar)
│   ├── css/
│   │   └── style.css        — All styles (responsive, pills, cards, entries list)
│   └── js/
│       └── app.js           — All frontend logic (API calls, DOM manipulation)
├── tools/
│   └── daily_journal_search.py  — Open WebUI tool script
├── scripts/
│   └── pull-models.sh       — Init script to pull Ollama models on first run
├── docker-compose.yml       — App + Ollama containers, volumes
├── data/                    — Mounted volume (gitignored)
│   ├── entries/             — MD files
│   └── db/                  — SQLite + ChromaDB storage
└── .gitignore
```

---

## Task 1: Project Scaffolding

**Files:**
- Create: `backend/main.py`
- Create: `backend/config.py`
- Create: `backend/requirements.txt`
- Create: `backend/Dockerfile`
- Create: `frontend/index.html`
- Create: `frontend/css/style.css`
- Create: `frontend/js/app.js`
- Create: `docker-compose.yml`
- Create: `scripts/pull-models.sh`
- Create: `.gitignore`

- [ ] **Step 1: Initialize git repo**

```bash
cd /mnt/c/Users/slavhate/journal-ai
git init
```

- [ ] **Step 2: Create .gitignore**

Create `.gitignore`:
```
data/
__pycache__/
*.pyc
.env
```

- [ ] **Step 3: Create backend/config.py**

```python
import os


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
DATA_DIR = os.getenv("DATA_DIR", "/data")
FORMATTING_MODEL = os.getenv("FORMATTING_MODEL", "llama3.2:3b")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
APP_PORT = int(os.getenv("APP_PORT", "8550"))
ENTRIES_DIR = os.path.join(DATA_DIR, "entries")
DB_DIR = os.path.join(DATA_DIR, "db")
SQLITE_PATH = os.path.join(DB_DIR, "journal.db")
CHROMADB_PATH = os.path.join(DB_DIR, "chromadb")
```

- [ ] **Step 4: Create backend/requirements.txt**

```
fastapi==0.115.6
uvicorn[standard]==0.32.1
httpx==0.28.1
chromadb==0.5.23
pydantic==2.10.4
```

- [ ] **Step 5: Create backend/main.py (minimal)**

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Journal AI")

app.mount("/", StaticFiles(directory="/app/frontend", html=True), name="frontend")
```

- [ ] **Step 6: Create backend/Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY frontend/ ./frontend/

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8550"]
```

- [ ] **Step 7: Create frontend/index.html (placeholder)**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Journal</title>
    <link rel="stylesheet" href="/css/style.css">
</head>
<body>
    <h1>Daily Journal</h1>
    <script src="/js/app.js"></script>
</body>
</html>
```

- [ ] **Step 8: Create frontend/css/style.css (placeholder)**

```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #f5f5f5;
    color: #333;
}
```

- [ ] **Step 9: Create frontend/js/app.js (placeholder)**

```javascript
document.addEventListener("DOMContentLoaded", () => {
    console.log("Journal AI loaded");
});
```

- [ ] **Step 10: Create scripts/pull-models.sh**

```bash
#!/bin/bash
set -e

OLLAMA_HOST="${OLLAMA_BASE_URL:-http://ollama:11434}"

echo "Waiting for Ollama to be ready..."
until curl -s "$OLLAMA_HOST/api/tags" > /dev/null 2>&1; do
    sleep 2
done

echo "Pulling llama3.2:3b..."
curl -s "$OLLAMA_HOST/api/pull" -d '{"name": "llama3.2:3b"}' | tail -1

echo "Pulling nomic-embed-text..."
curl -s "$OLLAMA_HOST/api/pull" -d '{"name": "nomic-embed-text"}' | tail -1

echo "Models ready."
```

- [ ] **Step 11: Create docker-compose.yml**

```yaml
services:
  app:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "8550:8550"
    volumes:
      - ./data:/data
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - DATA_DIR=/data
      - FORMATTING_MODEL=llama3.2:3b
      - EMBEDDING_MODEL=nomic-embed-text
    depends_on:
      - ollama

  ollama:
    image: ollama/ollama
    volumes:
      - ollama-models:/root/.ollama

volumes:
  ollama-models:
```

- [ ] **Step 12: Verify Docker build**

```bash
cd /mnt/c/Users/slavhate/journal-ai
docker compose build app
```

Expected: Build completes successfully.

- [ ] **Step 13: Commit**

```bash
git add .
git commit -m "feat: initial project scaffolding with Docker setup"
```

---

## Task 2: Database Layer

**Files:**
- Create: `backend/database.py`
- Create: `tests/test_database.py`

- [ ] **Step 1: Write failing test for database initialization**

Create `tests/test_database.py`:
```python
import os
import tempfile
import sqlite3
import pytest

os.environ["DATA_DIR"] = tempfile.mkdtemp()

from backend.database import init_db, get_db_path


def test_init_db_creates_tables():
    init_db()
    conn = sqlite3.connect(get_db_path())
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    assert "entries" in tables
    assert "events" in tables
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /mnt/c/Users/slavhate/journal-ai
pip install pytest fastapi uvicorn httpx chromadb pydantic
pytest tests/test_database.py -v
```

Expected: FAIL with ModuleNotFoundError or ImportError.

- [ ] **Step 3: Implement database.py**

Create `backend/database.py`:
```python
import sqlite3
from backend.config import SQLITE_PATH, DB_DIR, ENTRIES_DIR
import os


def get_db_path():
    return SQLITE_PATH


def get_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    os.makedirs(ENTRIES_DIR, exist_ok=True)
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS entries (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT NOT NULL,
            category    TEXT NOT NULL,
            raw_text    TEXT NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS events (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT NOT NULL,
            type        TEXT NOT NULL,
            title       TEXT NOT NULL,
            source_date TEXT NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_entries_date ON entries(date);
        CREATE INDEX IF NOT EXISTS idx_events_date ON events(date);
    """)
    conn.close()


def create_entry(date: str, category: str, raw_text: str) -> int:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO entries (date, category, raw_text) VALUES (?, ?, ?)",
        (date, category, raw_text)
    )
    entry_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return entry_id


def get_entries_by_date(date: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, date, category, raw_text, created_at FROM entries WHERE date = ? ORDER BY created_at",
        (date,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_entry(entry_id: int, raw_text: str) -> bool:
    conn = get_connection()
    cursor = conn.execute(
        "UPDATE entries SET raw_text = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (raw_text, entry_id)
    )
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated


def delete_entry(entry_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
    if row:
        conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        conn.commit()
    conn.close()
    return dict(row) if row else None


def create_event(date: str, event_type: str, title: str, source_date: str) -> int:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO events (date, type, title, source_date) VALUES (?, ?, ?, ?)",
        (date, event_type, title, source_date)
    )
    event_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return event_id


def get_events_by_date(date: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, date, type, title, source_date FROM events WHERE date = ?",
        (date,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_events_by_source_date(source_date: str):
    conn = get_connection()
    conn.execute("DELETE FROM events WHERE source_date = ?", (source_date,))
    conn.commit()
    conn.close()
```

- [ ] **Step 4: Add __init__.py files**

```bash
touch backend/__init__.py tests/__init__.py backend/routers/__init__.py
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/test_database.py -v
```

Expected: PASS

- [ ] **Step 6: Write tests for CRUD operations**

Append to `tests/test_database.py`:
```python
def test_create_and_get_entry():
    init_db()
    entry_id = create_entry("2026-05-05", "work", "Had standup meeting")
    entries = get_entries_by_date("2026-05-05")
    assert len(entries) >= 1
    found = [e for e in entries if e["id"] == entry_id]
    assert len(found) == 1
    assert found[0]["raw_text"] == "Had standup meeting"
    assert found[0]["category"] == "work"


def test_update_entry():
    init_db()
    entry_id = create_entry("2026-05-05", "work", "Original text")
    update_entry(entry_id, "Updated text")
    entries = get_entries_by_date("2026-05-05")
    found = [e for e in entries if e["id"] == entry_id]
    assert found[0]["raw_text"] == "Updated text"


def test_delete_entry():
    init_db()
    entry_id = create_entry("2026-05-06", "personal", "Gym session")
    deleted = delete_entry(entry_id)
    assert deleted is not None
    assert deleted["raw_text"] == "Gym session"
    entries = get_entries_by_date("2026-05-06")
    assert all(e["id"] != entry_id for e in entries)


def test_create_and_get_event():
    init_db()
    create_event("2026-05-10", "birthday", "Mom's birthday", "2026-05-05")
    events = get_events_by_date("2026-05-10")
    assert len(events) >= 1
    assert events[-1]["title"] == "Mom's birthday"
    assert events[-1]["type"] == "birthday"
```

Add imports at top:
```python
from backend.database import init_db, get_db_path, create_entry, get_entries_by_date, update_entry, delete_entry, create_event, get_events_by_date
```

- [ ] **Step 7: Run all database tests**

```bash
pytest tests/test_database.py -v
```

Expected: All PASS.

- [ ] **Step 8: Commit**

```bash
git add .
git commit -m "feat: add SQLite database layer with CRUD operations"
```

---

## Task 3: Ollama Service

**Files:**
- Create: `backend/ollama_service.py`
- Create: `tests/test_ollama_service.py`

- [ ] **Step 1: Write failing test for format_entry**

Create `tests/test_ollama_service.py`:
```python
import pytest
from unittest.mock import patch, AsyncMock
from backend.ollama_service import format_entry, generate_embedding


@pytest.mark.asyncio
async def test_format_entry_returns_structured_response():
    mock_response = {
        "response": '{"markdown": "### Standup\\n- Discussed timeline", "events": []}'
    }
    with patch("backend.ollama_service.call_ollama", new_callable=AsyncMock, return_value=mock_response):
        result = await format_entry(
            raw_text="Had standup, discussed timeline",
            category="work",
            existing_md=""
        )
        assert "markdown" in result
        assert "events" in result


@pytest.mark.asyncio
async def test_generate_embedding_returns_list():
    mock_response = {"embedding": [0.1, 0.2, 0.3]}
    with patch("backend.ollama_service.call_ollama_embedding", new_callable=AsyncMock, return_value=mock_response):
        result = await generate_embedding("some text")
        assert isinstance(result, list)
        assert len(result) > 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pip install pytest-asyncio
pytest tests/test_ollama_service.py -v
```

Expected: FAIL with ImportError.

- [ ] **Step 3: Implement ollama_service.py**

Create `backend/ollama_service.py`:
```python
import json
import httpx
from backend.config import OLLAMA_BASE_URL, FORMATTING_MODEL, EMBEDDING_MODEL


FORMATTING_PROMPT = """You are a journal entry formatter. Given a raw text entry and its category, do two things:

1. Format the entry as a markdown sub-section that fits under the category heading. Create an appropriate sub-heading (###) based on the topic. Format the content as bullet points.

2. Extract any future events, todos, or birthdays mentioned in the text.

Respond ONLY with valid JSON in this exact format:
{
  "markdown": "### Sub-heading\\n- Bullet point content",
  "events": [{"date": "YYYY-MM-DD", "type": "todo|birthday|event", "title": "short description"}]
}

If no events found, return empty events array. The markdown should NOT include the ## Category heading - only the ### sub-heading and bullets within it."""


async def call_ollama(prompt: str, system: str = "") -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": FORMATTING_MODEL,
                "prompt": prompt,
                "system": system,
                "stream": False
            }
        )
        response.raise_for_status()
        return response.json()


async def call_ollama_embedding(text: str) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={
                "model": EMBEDDING_MODEL,
                "prompt": text
            }
        )
        response.raise_for_status()
        return response.json()


async def format_entry(raw_text: str, category: str, existing_md: str) -> dict:
    context = f"Existing file content:\n{existing_md}\n\n" if existing_md else ""
    prompt = f"""{context}Category: {category}
Entry: {raw_text}

Format this entry as described."""

    response = await call_ollama(prompt, system=FORMATTING_PROMPT)
    raw_response = response.get("response", "{}")

    try:
        result = json.loads(raw_response)
    except json.JSONDecodeError:
        result = {"markdown": f"### Note\n- {raw_text}", "events": []}

    if "markdown" not in result:
        result["markdown"] = f"### Note\n- {raw_text}"
    if "events" not in result:
        result["events"] = []

    return result


async def generate_embedding(text: str) -> list[float]:
    response = await call_ollama_embedding(text)
    return response.get("embedding", [])
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_ollama_service.py -v
```

Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "feat: add Ollama service for entry formatting and embeddings"
```

---

## Task 4: Markdown Service

**Files:**
- Create: `backend/markdown_service.py`
- Create: `tests/test_markdown_service.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_markdown_service.py`:
```python
import os
import tempfile
import pytest

os.environ["DATA_DIR"] = tempfile.mkdtemp()

from backend.markdown_service import read_md_file, write_md_file, rebuild_md_file, remove_entry_from_md


def test_write_and_read_md_file():
    content = "# 2026-05-05\n\n## Work\n### Standup\n- Discussed timeline\n"
    write_md_file("2026-05-05", content)
    result = read_md_file("2026-05-05")
    assert result == content


def test_read_nonexistent_file_returns_empty():
    result = read_md_file("1999-01-01")
    assert result == ""


def test_rebuild_md_file_combines_sections():
    sections = {
        "work": ["### Standup\n- Discussed timeline", "### Reviews\n- Reviewed PR"],
        "personal": ["### Health\n- Morning run 5km"],
        "finance": []
    }
    result = rebuild_md_file("2026-05-05", sections)
    assert "# 2026-05-05" in result
    assert "## Work" in result
    assert "### Standup" in result
    assert "### Reviews" in result
    assert "## Personal" in result
    assert "### Health" in result
    assert "## Finance" not in result  # empty sections omitted
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_markdown_service.py -v
```

Expected: FAIL with ImportError.

- [ ] **Step 3: Implement markdown_service.py**

Create `backend/markdown_service.py`:
```python
import os
from backend.config import ENTRIES_DIR


def read_md_file(date: str) -> str:
    path = os.path.join(ENTRIES_DIR, f"{date}.md")
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_md_file(date: str, content: str):
    os.makedirs(ENTRIES_DIR, exist_ok=True)
    path = os.path.join(ENTRIES_DIR, f"{date}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def rebuild_md_file(date: str, sections: dict[str, list[str]]) -> str:
    lines = [f"# {date}\n"]
    category_order = ["work", "personal", "finance"]
    category_labels = {"work": "Work", "personal": "Personal", "finance": "Finance"}

    for cat in category_order:
        entries = sections.get(cat, [])
        if not entries:
            continue
        lines.append(f"\n## {category_labels[cat]}\n")
        for entry_md in entries:
            lines.append(f"{entry_md}\n")

    return "\n".join(lines)


def remove_entry_from_md(date: str, entry_text: str) -> str:
    content = read_md_file(date)
    if not content:
        return ""
    lines = content.split("\n")
    filtered = [line for line in lines if entry_text not in line]
    result = "\n".join(filtered)
    write_md_file(date, result)
    return result


def list_available_dates() -> list[str]:
    if not os.path.exists(ENTRIES_DIR):
        return []
    dates = []
    for filename in os.listdir(ENTRIES_DIR):
        if filename.endswith(".md"):
            dates.append(filename.replace(".md", ""))
    return sorted(dates, reverse=True)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_markdown_service.py -v
```

Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "feat: add markdown file service for read/write/rebuild"
```

---

## Task 5: ChromaDB Service

**Files:**
- Create: `backend/chromadb_service.py`
- Create: `tests/test_chromadb_service.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_chromadb_service.py`:
```python
import os
import tempfile
import pytest
from unittest.mock import patch, AsyncMock

os.environ["DATA_DIR"] = tempfile.mkdtemp()

from backend.chromadb_service import get_collection, upsert_document, query_documents


def test_get_collection_returns_collection():
    collection = get_collection()
    assert collection.name == "daily_entries"


def test_upsert_and_query_document():
    embedding = [0.1] * 384  # nomic-embed-text produces 768-dim, but for test use 384
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_chromadb_service.py -v
```

Expected: FAIL with ImportError.

- [ ] **Step 3: Implement chromadb_service.py**

Create `backend/chromadb_service.py`:
```python
import chromadb
from backend.config import CHROMADB_PATH
import os


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
    return collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_chromadb_service.py -v
```

Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "feat: add ChromaDB service for vector storage and search"
```

---

## Task 6: API Entries Router

**Files:**
- Create: `backend/routers/entries.py`
- Create: `tests/test_entries_router.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_entries_router.py`:
```python
import os
import tempfile
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

os.environ["DATA_DIR"] = tempfile.mkdtemp()

from backend.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_ollama():
    format_response = {"markdown": "### Note\n- Test entry", "events": []}
    embedding_response = [0.1] * 384
    with patch("backend.routers.entries.format_entry", new_callable=AsyncMock, return_value=format_response):
        with patch("backend.routers.entries.generate_embedding", new_callable=AsyncMock, return_value=embedding_response):
            with patch("backend.routers.entries.upsert_document"):
                yield


def test_create_entry():
    response = client.post("/api/entries", json={
        "category": "work",
        "raw_text": "Had standup meeting"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["id"] > 0
    assert data["category"] == "work"


def test_get_entries_by_date():
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
    resp = client.post("/api/entries", json={
        "category": "finance",
        "raw_text": "Paid rent"
    })
    entry_id = resp.json()["id"]
    del_resp = client.delete(f"/api/entries/{entry_id}")
    assert del_resp.status_code == 200
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_entries_router.py -v
```

Expected: FAIL with ImportError.

- [ ] **Step 3: Implement entries router**

Create `backend/routers/entries.py`:
```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import date

from backend.database import (
    create_entry, get_entries_by_date, update_entry, delete_entry,
    create_event, delete_events_by_source_date
)
from backend.ollama_service import format_entry, generate_embedding
from backend.markdown_service import read_md_file, write_md_file, rebuild_md_file
from backend.chromadb_service import upsert_document

router = APIRouter(prefix="/api/entries", tags=["entries"])


class EntryCreate(BaseModel):
    category: str
    raw_text: str


class EntryUpdate(BaseModel):
    raw_text: str


@router.post("")
async def create_entry_endpoint(entry: EntryCreate):
    today = date.today().isoformat()

    entry_id = create_entry(today, entry.category, entry.raw_text)

    existing_md = read_md_file(today)
    result = await format_entry(entry.raw_text, entry.category, existing_md)

    all_entries = get_entries_by_date(today)
    sections = {"work": [], "personal": [], "finance": []}
    for e in all_entries:
        if e["id"] == entry_id:
            sections[e["category"]].append(result["markdown"])
        else:
            sections[e["category"]].append(f"- {e['raw_text']}")

    # For proper rebuild, re-format all entries for that category
    # Simplified: append new formatted entry to existing MD
    if existing_md:
        category_header = f"## {entry.category.capitalize()}"
        if category_header in existing_md:
            insert_pos = existing_md.find(category_header) + len(category_header)
            next_section = existing_md.find("\n## ", insert_pos)
            if next_section == -1:
                new_md = existing_md.rstrip() + "\n" + result["markdown"] + "\n"
            else:
                new_md = (
                    existing_md[:next_section].rstrip() + "\n" + result["markdown"] + "\n" +
                    existing_md[next_section:]
                )
        else:
            new_md = existing_md.rstrip() + f"\n\n## {entry.category.capitalize()}\n{result['markdown']}\n"
    else:
        new_md = f"# {today}\n\n## {entry.category.capitalize()}\n{result['markdown']}\n"

    write_md_file(today, new_md)

    for event in result.get("events", []):
        create_event(event["date"], event["type"], event["title"], today)

    full_md = read_md_file(today)
    embedding = await generate_embedding(full_md)
    if embedding:
        categories = list(set(e["category"] for e in all_entries))
        upsert_document(today, full_md, embedding, categories)

    return {"id": entry_id, "category": entry.category, "raw_text": entry.raw_text}


@router.put("/{entry_id}")
async def update_entry_endpoint(entry_id: int, entry: EntryUpdate):
    updated = update_entry(entry_id, entry.raw_text)
    if not updated:
        raise HTTPException(status_code=404, detail="Entry not found")

    # Re-format entire day
    from backend.database import get_connection
    conn = get_connection()
    row = conn.execute("SELECT date FROM entries WHERE id = ?", (entry_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Entry not found")

    entry_date = row["date"]
    all_entries = get_entries_by_date(entry_date)

    sections = {"work": [], "personal": [], "finance": []}
    for e in all_entries:
        result = await format_entry(e["raw_text"], e["category"], "")
        sections[e["category"]].append(result["markdown"])

    new_md = rebuild_md_file(entry_date, sections)
    write_md_file(entry_date, new_md)

    # Re-extract events
    delete_events_by_source_date(entry_date)
    for e in all_entries:
        result = await format_entry(e["raw_text"], e["category"], "")
        for event in result.get("events", []):
            create_event(event["date"], event["type"], event["title"], entry_date)

    # Re-embed
    full_md = read_md_file(entry_date)
    embedding = await generate_embedding(full_md)
    if embedding:
        categories = list(set(e["category"] for e in all_entries))
        upsert_document(entry_date, full_md, embedding, categories)

    return {"status": "updated", "id": entry_id}


@router.delete("/{entry_id}")
async def delete_entry_endpoint(entry_id: int):
    deleted = delete_entry(entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entry not found")

    entry_date = deleted["date"]
    all_entries = get_entries_by_date(entry_date)

    if all_entries:
        sections = {"work": [], "personal": [], "finance": []}
        for e in all_entries:
            result = await format_entry(e["raw_text"], e["category"], "")
            sections[e["category"]].append(result["markdown"])
        new_md = rebuild_md_file(entry_date, sections)
    else:
        new_md = ""

    write_md_file(entry_date, new_md)

    # Re-embed
    if new_md:
        embedding = await generate_embedding(new_md)
        if embedding:
            categories = list(set(e["category"] for e in all_entries))
            upsert_document(entry_date, new_md, embedding, categories)

    return {"status": "deleted", "id": entry_id}


@router.get("/{date}")
async def get_entries_endpoint(date: str):
    entries = get_entries_by_date(date)
    grouped = {"work": [], "personal": [], "finance": []}
    for e in entries:
        grouped[e["category"]].append({
            "id": e["id"],
            "raw_text": e["raw_text"],
            "created_at": e["created_at"]
        })
    return grouped
```

- [ ] **Step 4: Update main.py to include router and init DB**

Update `backend/main.py`:
```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend.database import init_db
from backend.routers.entries import router as entries_router

app = FastAPI(title="Journal AI")

app.include_router(entries_router)


@app.on_event("startup")
def startup():
    init_db()


app.mount("/", StaticFiles(directory="/app/frontend", html=True), name="frontend")
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_entries_router.py -v
```

Expected: All PASS.

- [ ] **Step 6: Commit**

```bash
git add .
git commit -m "feat: add entries API router with create/edit/delete endpoints"
```

---

## Task 7: Days and Today Routers

**Files:**
- Create: `backend/routers/days.py`
- Create: `backend/routers/today.py`
- Create: `tests/test_days_router.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_days_router.py`:
```python
import os
import tempfile
import pytest
from fastapi.testclient import TestClient

os.environ["DATA_DIR"] = tempfile.mkdtemp()

from backend.main import app
from backend.database import init_db, create_event
from backend.markdown_service import write_md_file

client = TestClient(app)


def setup_module(module):
    init_db()
    write_md_file("2026-05-05", "# 2026-05-05\n\n## Work\n### Standup\n- Discussed timeline\n")


def test_get_days_list():
    response = client.get("/api/days")
    assert response.status_code == 200
    data = response.json()
    assert "2026-05-05" in data


def test_get_day_content():
    response = client.get("/api/days/2026-05-05")
    assert response.status_code == 200
    data = response.json()
    assert "content" in data
    assert "Standup" in data["content"]


def test_get_today_events():
    from datetime import date
    today = date.today().isoformat()
    create_event(today, "todo", "Submit report", "2026-05-04")
    response = client.get("/api/today")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[-1]["title"] == "Submit report"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_days_router.py -v
```

Expected: FAIL with ImportError.

- [ ] **Step 3: Implement days router**

Create `backend/routers/days.py`:
```python
from fastapi import APIRouter, HTTPException
from backend.markdown_service import read_md_file, list_available_dates

router = APIRouter(prefix="/api/days", tags=["days"])


@router.get("")
async def get_available_days():
    return list_available_dates()


@router.get("/{date}")
async def get_day_content(date: str):
    content = read_md_file(date)
    if not content:
        raise HTTPException(status_code=404, detail="No entries for this date")
    return {"date": date, "content": content}
```

- [ ] **Step 4: Implement today router**

Create `backend/routers/today.py`:
```python
from fastapi import APIRouter
from datetime import date
from backend.database import get_events_by_date

router = APIRouter(tags=["today"])


@router.get("/api/today")
async def get_today_events():
    today = date.today().isoformat()
    return get_events_by_date(today)
```

- [ ] **Step 5: Update main.py to include new routers**

Update `backend/main.py`:
```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend.database import init_db
from backend.routers.entries import router as entries_router
from backend.routers.days import router as days_router
from backend.routers.today import router as today_router

app = FastAPI(title="Journal AI")

app.include_router(entries_router)
app.include_router(days_router)
app.include_router(today_router)


@app.on_event("startup")
def startup():
    init_db()


app.mount("/", StaticFiles(directory="/app/frontend", html=True), name="frontend")
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
pytest tests/test_days_router.py -v
```

Expected: All PASS.

- [ ] **Step 7: Commit**

```bash
git add .
git commit -m "feat: add days and today API routers"
```

---

## Task 8: Frontend — Full UI

**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/css/style.css`
- Modify: `frontend/js/app.js`

- [ ] **Step 1: Implement index.html**

Replace `frontend/index.html`:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Journal</title>
    <link rel="stylesheet" href="/css/style.css">
</head>
<body>
    <header>
        <h1>Daily Journal</h1>
        <input type="date" id="date-picker">
    </header>

    <div class="container">
        <main class="main-column">
            <div class="category-pills">
                <button class="pill active" data-category="work">Work</button>
                <button class="pill" data-category="personal">Personal</button>
                <button class="pill" data-category="finance">Finance</button>
            </div>

            <div class="entry-form">
                <input type="text" id="entry-input" placeholder="Type your entry..." autocomplete="off">
                <button id="submit-btn">Submit</button>
            </div>

            <div class="entries-section">
                <h2>Today's Entries</h2>
                <div id="entries-list"></div>
            </div>
        </main>

        <aside class="sidebar">
            <div class="glance-card">
                <h3>Day in Glance</h3>
                <div id="events-list">
                    <p class="empty-state">No events today</p>
                </div>
            </div>
        </aside>
    </div>

    <script src="/js/app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Implement style.css**

Replace `frontend/css/style.css`:
```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #f5f5f5;
    color: #333;
    min-height: 100vh;
}

header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 2rem;
    background: #fff;
    border-bottom: 1px solid #e0e0e0;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

header h1 {
    font-size: 1.5rem;
    font-weight: 600;
}

#date-picker {
    padding: 0.5rem;
    border: 1px solid #ddd;
    border-radius: 6px;
    font-size: 0.9rem;
}

.container {
    display: flex;
    gap: 2rem;
    max-width: 1200px;
    margin: 2rem auto;
    padding: 0 2rem;
}

.main-column {
    flex: 7;
}

.sidebar {
    flex: 3;
}

.category-pills {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
}

.pill {
    padding: 0.5rem 1.25rem;
    border: 2px solid #ddd;
    border-radius: 20px;
    background: #fff;
    cursor: pointer;
    font-size: 0.9rem;
    font-weight: 500;
    transition: all 0.2s;
}

.pill:hover {
    border-color: #666;
}

.pill.active {
    background: #333;
    color: #fff;
    border-color: #333;
}

.entry-form {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 2rem;
}

#entry-input {
    flex: 1;
    padding: 0.75rem 1rem;
    border: 1px solid #ddd;
    border-radius: 8px;
    font-size: 1rem;
    outline: none;
    transition: border-color 0.2s;
}

#entry-input:focus {
    border-color: #333;
}

#submit-btn {
    padding: 0.75rem 1.5rem;
    background: #333;
    color: #fff;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.9rem;
    font-weight: 500;
    transition: background 0.2s;
}

#submit-btn:hover {
    background: #555;
}

#submit-btn:disabled {
    background: #999;
    cursor: not-allowed;
}

.entries-section h2 {
    font-size: 1.1rem;
    margin-bottom: 1rem;
    color: #666;
}

.category-group {
    margin-bottom: 1.5rem;
}

.category-group h3 {
    font-size: 0.9rem;
    font-weight: 600;
    text-transform: uppercase;
    color: #888;
    margin-bottom: 0.5rem;
    letter-spacing: 0.5px;
}

.entry-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.6rem 0;
    border-bottom: 1px solid #eee;
}

.entry-item:last-child {
    border-bottom: none;
}

.entry-text {
    flex: 1;
}

.entry-actions {
    display: flex;
    gap: 0.5rem;
}

.entry-actions button {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 1rem;
    padding: 0.25rem;
    opacity: 0.5;
    transition: opacity 0.2s;
}

.entry-actions button:hover {
    opacity: 1;
}

.edit-form {
    display: flex;
    gap: 0.5rem;
    width: 100%;
}

.edit-form input {
    flex: 1;
    padding: 0.4rem 0.6rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 0.9rem;
}

.edit-form button {
    padding: 0.4rem 0.8rem;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.8rem;
}

.edit-form .save-btn {
    background: #333;
    color: #fff;
}

.edit-form .cancel-btn {
    background: #eee;
}

.glance-card {
    background: #fff;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    position: sticky;
    top: 2rem;
}

.glance-card h3 {
    font-size: 1rem;
    margin-bottom: 1rem;
    color: #333;
}

.event-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0;
    border-bottom: 1px solid #f0f0f0;
    font-size: 0.9rem;
}

.event-item:last-child {
    border-bottom: none;
}

.event-icon {
    font-size: 1.1rem;
}

.empty-state {
    color: #aaa;
    font-size: 0.9rem;
    font-style: italic;
}

.read-only-notice {
    background: #fff3cd;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    font-size: 0.85rem;
    color: #856404;
    margin-bottom: 1rem;
}

@media (max-width: 768px) {
    .container {
        flex-direction: column;
    }

    .sidebar {
        order: -1;
    }

    header {
        padding: 1rem;
    }

    .container {
        padding: 0 1rem;
    }
}
```

- [ ] **Step 3: Implement app.js**

Replace `frontend/js/app.js`:
```javascript
document.addEventListener("DOMContentLoaded", () => {
    const datePicker = document.getElementById("date-picker");
    const entryInput = document.getElementById("entry-input");
    const submitBtn = document.getElementById("submit-btn");
    const entriesList = document.getElementById("entries-list");
    const eventsList = document.getElementById("events-list");
    const pills = document.querySelectorAll(".pill");

    let selectedCategory = "work";
    let isToday = true;

    const today = new Date().toISOString().split("T")[0];
    datePicker.value = today;

    function getSelectedDate() {
        return datePicker.value;
    }

    pills.forEach(pill => {
        pill.addEventListener("click", () => {
            pills.forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            selectedCategory = pill.dataset.category;
        });
    });

    async function submitEntry() {
        const text = entryInput.value.trim();
        if (!text) return;

        submitBtn.disabled = true;
        submitBtn.textContent = "Saving...";

        try {
            const response = await fetch("/api/entries", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ category: selectedCategory, raw_text: text })
            });

            if (response.ok) {
                entryInput.value = "";
                await loadEntries(today);
                await loadEvents();
            }
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = "Submit";
        }
    }

    submitBtn.addEventListener("click", submitEntry);
    entryInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") submitEntry();
    });

    async function loadEntries(date) {
        const response = await fetch(`/api/entries/${date}`);
        if (!response.ok) {
            entriesList.innerHTML = '<p class="empty-state">No entries yet</p>';
            return;
        }
        const data = await response.json();
        renderEntries(data, date === today);
    }

    function renderEntries(grouped, editable) {
        const categories = ["work", "personal", "finance"];
        const labels = { work: "Work", personal: "Personal", finance: "Finance" };
        let html = "";

        for (const cat of categories) {
            const entries = grouped[cat] || [];
            if (entries.length === 0) continue;

            html += `<div class="category-group"><h3>${labels[cat]}</h3>`;
            for (const entry of entries) {
                html += `<div class="entry-item" data-id="${entry.id}">`;
                html += `<span class="entry-text">${escapeHtml(entry.raw_text)}</span>`;
                if (editable) {
                    html += `<div class="entry-actions">`;
                    html += `<button onclick="editEntry(${entry.id}, '${escapeAttr(entry.raw_text)}')">&#9998;</button>`;
                    html += `<button onclick="deleteEntry(${entry.id})">&#10005;</button>`;
                    html += `</div>`;
                }
                html += `</div>`;
            }
            html += `</div>`;
        }

        if (!html) {
            html = '<p class="empty-state">No entries yet</p>';
        }

        entriesList.innerHTML = html;
    }

    async function loadEvents() {
        const response = await fetch("/api/today");
        if (!response.ok) return;
        const events = await response.json();

        if (events.length === 0) {
            eventsList.innerHTML = '<p class="empty-state">No events today</p>';
            return;
        }

        const icons = { todo: "☐", birthday: "🎂", event: "📅" };
        let html = "";
        for (const event of events) {
            const icon = icons[event.type] || "•";
            html += `<div class="event-item"><span class="event-icon">${icon}</span><span>${escapeHtml(event.title)}</span></div>`;
        }
        eventsList.innerHTML = html;
    }

    datePicker.addEventListener("change", () => {
        const date = getSelectedDate();
        isToday = date === today;

        const formSection = document.querySelector(".entry-form");
        const pillsSection = document.querySelector(".category-pills");
        const heading = document.querySelector(".entries-section h2");

        if (isToday) {
            formSection.style.display = "flex";
            pillsSection.style.display = "flex";
            heading.textContent = "Today's Entries";
            const notice = document.querySelector(".read-only-notice");
            if (notice) notice.remove();
        } else {
            formSection.style.display = "none";
            pillsSection.style.display = "none";
            heading.textContent = `Entries for ${date}`;
            if (!document.querySelector(".read-only-notice")) {
                const notice = document.createElement("div");
                notice.className = "read-only-notice";
                notice.textContent = "Viewing past entries (read-only)";
                document.querySelector(".entries-section").prepend(notice);
            }
        }

        loadEntries(date);
    });

    window.editEntry = function(id, currentText) {
        const item = document.querySelector(`[data-id="${id}"]`);
        item.innerHTML = `
            <div class="edit-form">
                <input type="text" value="${escapeAttr(currentText)}" id="edit-input-${id}">
                <button class="save-btn" onclick="saveEdit(${id})">Save</button>
                <button class="cancel-btn" onclick="loadEntries('${today}')">Cancel</button>
            </div>
        `;
        document.getElementById(`edit-input-${id}`).focus();
    };

    window.saveEdit = async function(id) {
        const input = document.getElementById(`edit-input-${id}`);
        const newText = input.value.trim();
        if (!newText) return;

        const response = await fetch(`/api/entries/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ raw_text: newText })
        });

        if (response.ok) {
            await loadEntries(today);
        }
    };

    window.deleteEntry = async function(id) {
        const response = await fetch(`/api/entries/${id}`, { method: "DELETE" });
        if (response.ok) {
            await loadEntries(today);
        }
    };

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    function escapeAttr(text) {
        return text.replace(/'/g, "\\'").replace(/"/g, "&quot;");
    }

    loadEntries(today);
    loadEvents();
});
```

- [ ] **Step 4: Verify build still works**

```bash
cd /mnt/c/Users/slavhate/journal-ai
docker compose build app
```

Expected: Build succeeds.

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "feat: implement full frontend UI with entry form and day in glance"
```

---

## Task 9: Open WebUI Tool Script

**Files:**
- Create: `tools/daily_journal_search.py`

- [ ] **Step 1: Implement the tool script**

Create `tools/daily_journal_search.py`:
```python
"""
title: Daily Journal Search
description: Searches personal daily journal entries using semantic similarity via ChromaDB and Ollama embeddings.
author: journal-ai
version: 0.1.0
"""

import os
import re
import httpx
import chromadb
from datetime import datetime, timedelta


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
DATA_DIR = os.getenv("DATA_DIR", "/data")
CHROMADB_PATH = os.path.join(DATA_DIR, "db", "chromadb")
ENTRIES_DIR = os.path.join(DATA_DIR, "entries")


class Tools:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=CHROMADB_PATH)
        self.collection = self.client.get_or_create_collection("daily_entries")

    async def search_journal(self, query: str) -> str:
        """
        Search daily journal entries by semantic similarity.
        Use this to find information from past journal entries.

        :param query: Natural language query about journal content
        :return: Relevant journal entries as context
        """
        embedding = await self._get_embedding(query)
        if not embedding:
            return "Error: Could not generate embedding for query."

        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=5,
            include=["documents", "metadatas", "distances"]
        )

        # Also check for explicit date references
        date_files = self._extract_date_files(query)

        documents = []

        # Add date-explicit files
        for date_str in date_files:
            content = self._read_md_file(date_str)
            if content and content not in documents:
                documents.append(content)

        # Add semantic results
        if results["documents"] and results["documents"][0]:
            for doc in results["documents"][0]:
                if doc and doc not in documents:
                    documents.append(doc)

        if not documents:
            return "No matching journal entries found."

        # Limit total context
        combined = "\n\n---\n\n".join(documents[:5])
        if len(combined) > 8000:
            combined = combined[:8000] + "\n\n[Truncated for context length]"

        return combined

    async def _get_embedding(self, text: str) -> list[float]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{OLLAMA_BASE_URL}/api/embeddings",
                    json={"model": EMBEDDING_MODEL, "prompt": text}
                )
                response.raise_for_status()
                return response.json().get("embedding", [])
            except Exception:
                return []

    def _read_md_file(self, date_str: str) -> str:
        path = os.path.join(ENTRIES_DIR, f"{date_str}.md")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def _extract_date_files(self, query: str) -> list[str]:
        dates = []
        today = datetime.now()

        # Match "YYYY-MM-DD"
        iso_matches = re.findall(r"\d{4}-\d{2}-\d{2}", query)
        dates.extend(iso_matches)

        # Match relative references
        lower = query.lower()
        if "yesterday" in lower:
            dates.append((today - timedelta(days=1)).strftime("%Y-%m-%d"))
        if "today" in lower:
            dates.append(today.strftime("%Y-%m-%d"))
        if "last week" in lower:
            for i in range(7, 14):
                dates.append((today - timedelta(days=i)).strftime("%Y-%m-%d"))

        # Match "May 3rd", "March 15" etc.
        month_pattern = r"(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})"
        month_matches = re.findall(month_pattern, lower)
        month_map = {
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12
        }
        for month_name, day in month_matches:
            month_num = month_map[month_name]
            year = today.year
            dates.append(f"{year}-{month_num:02d}-{int(day):02d}")

        return list(set(dates))
```

- [ ] **Step 2: Commit**

```bash
git add .
git commit -m "feat: add Open WebUI tool script for semantic journal search"
```

---

## Task 10: Integration Test & Docker Compose Verification

**Files:**
- Modify: `docker-compose.yml` (add model pull init)
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write integration test**

Create `tests/test_integration.py`:
```python
import os
import tempfile
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

os.environ["DATA_DIR"] = tempfile.mkdtemp()

from backend.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_ollama_services():
    format_response = {"markdown": "### Meeting\n- Discussed project timeline", "events": [{"date": "2026-05-10", "type": "todo", "title": "Submit report"}]}
    embedding = [0.1] * 384

    with patch("backend.routers.entries.format_entry", new_callable=AsyncMock, return_value=format_response):
        with patch("backend.routers.entries.generate_embedding", new_callable=AsyncMock, return_value=embedding):
            with patch("backend.routers.entries.upsert_document"):
                yield


def test_full_entry_lifecycle():
    # Create
    resp = client.post("/api/entries", json={"category": "work", "raw_text": "Had project meeting, need to submit report by May 10"})
    assert resp.status_code == 200
    entry_id = resp.json()["id"]

    # Read
    from datetime import date
    today = date.today().isoformat()
    resp = client.get(f"/api/entries/{today}")
    assert resp.status_code == 200
    assert len(resp.json()["work"]) >= 1

    # Check today events
    resp = client.get("/api/today")
    assert resp.status_code == 200

    # Edit
    resp = client.put(f"/api/entries/{entry_id}", json={"raw_text": "Updated: project meeting went well"})
    assert resp.status_code == 200

    # Delete
    resp = client.delete(f"/api/entries/{entry_id}")
    assert resp.status_code == 200

    # Check days list
    resp = client.get("/api/days")
    assert resp.status_code == 200


def test_static_frontend_served():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Daily Journal" in resp.text
```

- [ ] **Step 2: Run all tests**

```bash
cd /mnt/c/Users/slavhate/journal-ai
pytest tests/ -v
```

Expected: All PASS.

- [ ] **Step 3: Update docker-compose.yml with model pull init**

Update `docker-compose.yml`:
```yaml
services:
  app:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "8550:8550"
    volumes:
      - ./data:/data
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - DATA_DIR=/data
      - FORMATTING_MODEL=llama3.2:3b
      - EMBEDDING_MODEL=nomic-embed-text
    depends_on:
      ollama:
        condition: service_started

  ollama:
    image: ollama/ollama
    volumes:
      - ollama-models:/root/.ollama
    ports:
      - "11434:11434"

  model-pull:
    image: curlimages/curl:latest
    depends_on:
      ollama:
        condition: service_started
    restart: "no"
    entrypoint: ["/bin/sh", "-c"]
    command:
      - |
        echo "Waiting for Ollama..."
        until curl -s http://ollama:11434/api/tags > /dev/null 2>&1; do sleep 2; done
        echo "Pulling llama3.2:3b..."
        curl -s http://ollama:11434/api/pull -d '{"name":"llama3.2:3b"}'
        echo "Pulling nomic-embed-text..."
        curl -s http://ollama:11434/api/pull -d '{"name":"nomic-embed-text"}'
        echo "Done."

volumes:
  ollama-models:
```

- [ ] **Step 4: Full Docker Compose build and verify**

```bash
cd /mnt/c/Users/slavhate/journal-ai
docker compose build
```

Expected: Build succeeds.

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "feat: add integration tests and finalize Docker Compose setup"
```

---

## Task 11: End-to-End Smoke Test

- [ ] **Step 1: Start the full stack**

```bash
cd /mnt/c/Users/slavhate/journal-ai
docker compose up -d
```

- [ ] **Step 2: Wait for models to pull (first time only)**

```bash
docker compose logs -f model-pull
```

Wait until it prints "Done."

- [ ] **Step 3: Test the API manually**

```bash
# Create an entry
curl -X POST http://localhost:8550/api/entries \
  -H "Content-Type: application/json" \
  -d '{"category": "work", "raw_text": "Had standup meeting, discussed project timeline"}'

# Get today's entries
curl http://localhost:8550/api/entries/$(date +%Y-%m-%d)

# Check today's events
curl http://localhost:8550/api/today

# Check days list
curl http://localhost:8550/api/days
```

- [ ] **Step 4: Open browser and verify UI**

Open `http://localhost:8550` in a browser. Verify:
- Category pills are visible and clickable
- Text input works
- Submit creates an entry and it appears in the list below
- Day in Glance card shows any extracted events
- Date picker switches to read-only mode for past dates

- [ ] **Step 5: Commit any fixes and tag**

```bash
git add .
git commit -m "chore: smoke test passed, system operational"
git tag v0.1.0
```

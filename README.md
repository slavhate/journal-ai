# Daily Journal AI

A personal daily journaling app with AI-powered entry formatting and semantic search.

Write plain-text entries throughout the day — an LLM formats them into structured Markdown files (one per day). A vector search tool in Open WebUI lets you query your journal history with natural language.

## Features

- **Category-based entries** — Work, Personal, Finance
- **AI formatting** — Ollama (`llama3.2:3b`) formats raw text into structured Markdown sub-sections
- **Event extraction** — Automatically extracts todos, birthdays, and upcoming events from entries
- **Day in Glance** — Sidebar shows today's extracted events
- **Date picker** — Browse past days in read-only mode
- **Semantic search** — Open WebUI tool queries ChromaDB for relevant journal history
- **Offline / self-hosted** — Everything runs locally via Docker Compose

## Architecture

```
docker-compose.yml
┌──────────────────────────────────────────────┐
│  app (FastAPI + static frontend)             │
│    └── /data volume                          │
│         ├── entries/   (YYYY-MM-DD.md files) │
│         └── db/        (SQLite + ChromaDB)   │
│  ollama  (llama3.2:3b, nomic-embed-text)     │
│  model-pull  (init: pulls models on startup) │
└──────────────────────────────────────────────┘
```

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI (Python 3.11) |
| Frontend | Vanilla HTML/JS/CSS |
| AI Formatting | Ollama — `llama3.2:3b` |
| Embeddings | Ollama — `nomic-embed-text` |
| Vector DB | ChromaDB (file-based) |
| Relational DB | SQLite |
| Deployment | Docker Compose |

## Quick Start

```bash
docker compose up -d
```

On first run the `model-pull` service pulls `llama3.2:3b` and `nomic-embed-text` from Ollama (~3 GB total). Wait for it to finish before submitting entries:

```bash
docker compose logs -f model-pull
# Wait for "Done."
```

Open **http://localhost:8550** in your browser.

## Configuration

Set these in `docker-compose.yml` under the `app` service:

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama API endpoint |
| `DATA_DIR` | `/data` | Data directory (MD files, SQLite, ChromaDB) |
| `FORMATTING_MODEL` | `llama3.2:3b` | Model for entry formatting |
| `EMBEDDING_MODEL` | `nomic-embed-text` | Model for embeddings |
| `APP_PORT` | `8550` | Web UI port |

## API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/entries` | Create entry |
| `PUT` | `/api/entries/{id}` | Edit entry |
| `DELETE` | `/api/entries/{id}` | Delete entry |
| `GET` | `/api/entries/{date}` | Get entries for a date |
| `GET` | `/api/today` | Today's extracted events |
| `GET` | `/api/days/{date}` | Formatted Markdown for a date |
| `GET` | `/api/days` | List all available dates |

## Open WebUI Integration

Register `tools/daily_journal_search.py` as a tool in Open WebUI. It embeds your query with `nomic-embed-text`, queries ChromaDB for the top 5 matching days, and returns the Markdown content as context. Supports ISO dates, relative terms (`yesterday`, `last week`), and month/day references (`May 3rd`).

## Data & Backup

All user data lives in `./data/` — copy this directory to back up everything.

```
data/
├── entries/        # Markdown files (one per day)
└── db/
    ├── journal.db  # SQLite (raw entries + events)
    └── chromadb/   # Vector embeddings
```

## Development

Install dependencies and run tests:

```bash
pip install -r backend/requirements.txt pytest pytest-asyncio
python3 -m pytest tests/ -v
```

Run the app locally (without Docker):

```bash
DATA_DIR=./data FRONTEND_DIR=./frontend OLLAMA_BASE_URL=http://localhost:11434 \
  uvicorn backend.main:app --host 0.0.0.0 --port 8550 --reload
```

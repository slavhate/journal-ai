# Daily Journal AI — Design Spec

## Overview

A personal daily journaling system with AI-powered formatting and semantic search. Users enter plain-text entries categorized as work, personal, or finance throughout the day. An LLM formats entries into structured Markdown files (one per day). A vector-search tool in Open WebUI enables natural language querying across all historical entries.

## Architecture

### System Diagram

```
docker-compose.yml
┌─────────────────────────────────────────────────────┐
│                                                     │
│  ┌───────────────────┐     ┌──────────────────┐    │
│  │   app container    │     │  ollama container │    │
│  │   (FastAPI +       │────▶│  (llama3.2:3b,   │    │
│  │    static frontend)│     │   nomic-embed-   │    │
│  │                    │     │   text)           │    │
│  └────────┬───────────┘     └──────────────────┘    │
│           │                                         │
│           ▼                                         │
│  ┌────────────────────────────────────────┐         │
│  │  ./data volume                         │         │
│  │  ├── entries/        (MD files)        │         │
│  │  └── db/             (SQLite + ChromaDB)│        │
│  └────────────────────────────────────────┘         │
│           ▲                                         │
│  ┌────────┴──────────┐                              │
│  │  open-webui        │ (shared volume mount)       │
│  │  + tool script     │                             │
│  └───────────────────┘                              │
└─────────────────────────────────────────────────────┘
```

### Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI (Python 3.11) |
| Frontend | Vanilla HTML/JS/CSS (served by FastAPI) |
| AI Formatting | Ollama — `llama3.2:3b` |
| Embeddings | Ollama — `nomic-embed-text` |
| Query Answering | Open WebUI — `llama3.1:8b` |
| Vector DB | ChromaDB (file-based) |
| Relational DB | SQLite |
| Deployment | Docker Compose |
| Target Hardware | Mac Mini 32GB (production), WSL (development) |

### Containers

1. **app** — Python 3.11-slim, runs FastAPI, serves static frontend, manages all data
2. **ollama** — Official `ollama/ollama` image, exposes API on internal Docker network
3. **open-webui** — Existing Open WebUI instance with custom tool script

### Volumes

- `./data/entries/` — Markdown files (flat structure: `2026-05-05.md`)
- `./data/db/` — SQLite database + ChromaDB persistent storage
- `ollama-models` — Named volume for downloaded Ollama models

## Data Model

### SQLite Schema

```sql
CREATE TABLE entries (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date        TEXT NOT NULL,           -- "2026-05-05"
    category    TEXT NOT NULL,           -- "work" | "personal" | "finance"
    raw_text    TEXT NOT NULL,           -- original user input
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date        TEXT NOT NULL,           -- date the event is FOR
    type        TEXT NOT NULL,           -- "todo" | "birthday" | "event"
    title       TEXT NOT NULL,           -- short description
    source_date TEXT NOT NULL,           -- which day's entry it was extracted from
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_entries_date ON entries(date);
CREATE INDEX idx_events_date ON events(date);
```

### ChromaDB Collection

- Collection name: `daily_entries`
- Document: Full MD content of a day's file
- Metadata: `{date: "2026-05-05", categories: ["work", "personal", "finance"]}`
- Embedding model: `nomic-embed-text` via Ollama
- Re-embedded on any change to the day's entries (create, edit, delete)

### Markdown File Format

```markdown
# 2026-05-05

## Work
### Project Alpha
- Discussed timeline in standup, deadline moved to June

### Code Reviews
- Reviewed auth module PR, suggested token refresh fix

## Personal
### Health
- Morning run 5km, new personal best

## Finance
### Expenses
- Groceries ₹1200 at DMart

### Investments
- Monthly SIP executed for May
```

Structure rules:
- Three fixed top-level sections: `## Work`, `## Personal`, `## Finance`
- AI creates sub-headings within each section based on content grouping
- Empty sections are omitted

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/entries` | Create entry (triggers AI format + embed) |
| PUT | `/api/entries/{id}` | Edit entry (triggers AI re-format + re-embed) |
| DELETE | `/api/entries/{id}` | Delete entry (surgical MD update + re-embed) |
| GET | `/api/entries/{date}` | Get entries for a date (grouped by category) |
| GET | `/api/today` | Day in Glance card data (events for today) |
| GET | `/api/days/{date}` | Get formatted MD content for a past date |
| GET | `/api/days` | List available dates (for calendar/date picker) |

### Entry Creation Flow

1. User submits entry with category selection
2. `POST /api/entries` saves raw entry to SQLite `entries` table
3. Backend calls Ollama (`llama3.2:3b`) with:
   - The new entry text and category
   - Existing MD file content for today (for context/merging)
   - Prompt: format entry, integrate into appropriate section, extract future events
4. AI returns: updated MD content + extracted events (if any)
5. Backend writes updated MD file to `./data/entries/{date}.md`
6. Backend inserts extracted events into SQLite `events` table
7. Backend calls Ollama (`nomic-embed-text`) to embed the full day's MD
8. Backend upserts embedding in ChromaDB
9. Returns success + updated grouped entries to UI

### Edit Flow

- Update raw text in SQLite
- Re-format entire day's MD file (all entries re-processed through AI)
- Re-embed in ChromaDB

### Delete Flow

- Remove entry from SQLite
- Remove corresponding content from MD file (surgical, no AI call)
- Re-embed in ChromaDB

## Frontend UI

### Layout

```
┌─────────────────────────────────────────────────────────┐
│  Header: "Daily Journal"              [Date Picker]      │
├─────────────────────────────────────┬───────────────────┤
│         Main Column (70%)            │  Sidebar (30%)    │
│                                      │                   │
│  [● Work] [○ Personal] [○ Finance]  │  Day in Glance   │
│                                      │  ─────────────   │
│  ┌─────────────────────────────┐    │  • Mom's bday    │
│  │ Type your entry...    [Submit]│   │  • Submit report │
│  └─────────────────────────────┘    │  • Team offsite  │
│                                      │                   │
│  ── Today's Entries ──────────────   │                   │
│                                      │                   │
│  Work                                │                   │
│  • Standup: timeline moved   [✎][✕] │                   │
│  • Reviewed auth PR          [✎][✕] │                   │
│                                      │                   │
│  Personal                            │                   │
│  • Morning run 5km, PB       [✎][✕] │                   │
│                                      │                   │
│  Finance                             │                   │
│  • Groceries ₹1200           [✎][✕] │                   │
│                                      │                   │
└─────────────────────────────────────┴───────────────────┘
```

### UI Behaviors

- **Category selection:** Radio-style pill buttons, always visible, one selected at a time, defaults to "Work"
- **Entry submission:** Submit button or Enter key
- **Today's entries:** Grouped by category, each entry shows edit (✎) and delete (✕) icons
- **Edit mode:** Inline text box with raw text pre-filled, save re-triggers AI formatting
- **Date picker:** Browse past days in read-only mode (no edit/delete icons shown)
- **Day in Glance card:** Displays events, todos, birthdays for current date from `GET /api/today`
- **Mobile responsive:** Sidebar stacks below main column on small screens

## Open WebUI Integration

### Tool Script

A Python tool registered in Open WebUI that provides semantic search over journal history:

```python
class DailyJournalSearch:
    """
    Searches personal daily journal entries using semantic similarity.
    Accesses ChromaDB at /data/db/chromadb and MD files at /data/entries/.
    """

    def search(self, query: str) -> str:
        # 1. Embed query using nomic-embed-text via Ollama
        # 2. Query ChromaDB for top 5 similar days
        # 3. If query contains parseable date, include that file directly
        # 4. Read matching MD files
        # 5. Return concatenated content as context for LLM
```

### Query Handling

- **Semantic queries** ("when did I discuss project Alpha?") — pure vector search
- **Date-explicit queries** ("what happened on May 3rd?") — parse date, fetch that file directly + semantic results
- **Large context mitigation** — if 5 full files exceed reasonable token limits, return only relevant sections

### Scalability

- ChromaDB handles thousands of embeddings with sub-second query times
- Only top-N files loaded per query, never full history
- Embedding cost is at write time (once per entry change), not query time
- Single-user personal journal unlikely to exceed ChromaDB's comfortable range even after years

## Deployment

### First Run

1. `docker compose up -d`
2. Ollama container pulls `llama3.2:3b` and `nomic-embed-text` on first startup (init script)
3. App container creates SQLite tables and ChromaDB collection on first request
4. Frontend accessible at `http://localhost:<port>`

### Backup

All user data is in `./data/` — copy this directory to back up everything (MD files, SQLite, ChromaDB).

### Configuration

Environment variables in `docker-compose.yml`:
- `OLLAMA_BASE_URL` — Ollama API URL (default: `http://ollama:11434`)
- `DATA_DIR` — data directory path (default: `/data`)
- `FORMATTING_MODEL` — model for entry formatting (default: `llama3.2:3b`)
- `EMBEDDING_MODEL` — model for embeddings (default: `nomic-embed-text`)
- `APP_PORT` — port for the web UI (default: `8550`)

import sqlite3
import os
from contextlib import contextmanager
from backend.config import SQLITE_PATH, DB_DIR, ENTRIES_DIR


def get_db_path():
    return SQLITE_PATH


@contextmanager
def db_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(SQLITE_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    os.makedirs(ENTRIES_DIR, exist_ok=True)
    with db_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS entries (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                date         TEXT NOT NULL,
                category     TEXT NOT NULL,
                raw_text     TEXT NOT NULL,
                formatted_md TEXT,
                created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        # Migrate existing DB: add formatted_md column if missing
        try:
            conn.execute("ALTER TABLE entries ADD COLUMN formatted_md TEXT")
            conn.commit()
        except Exception:
            pass


def create_entry(date: str, category: str, raw_text: str, formatted_md: str = None) -> int:
    with db_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO entries (date, category, raw_text, formatted_md) VALUES (?, ?, ?, ?)",
            (date, category, raw_text, formatted_md)
        )
        entry_id = cursor.lastrowid
        conn.commit()
    return entry_id


def update_entry_formatted_md(entry_id: int, formatted_md: str):
    with db_connection() as conn:
        conn.execute(
            "UPDATE entries SET formatted_md = ? WHERE id = ?",
            (formatted_md, entry_id)
        )
        conn.commit()


def get_entries_by_date(date: str) -> list[dict]:
    with db_connection() as conn:
        rows = conn.execute(
            "SELECT id, date, category, raw_text, formatted_md, created_at FROM entries WHERE date = ? ORDER BY created_at",
            (date,)
        ).fetchall()
    return [dict(row) for row in rows]


def get_entry_by_id(entry_id: int) -> dict | None:
    with db_connection() as conn:
        row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
    return dict(row) if row else None


def update_entry(entry_id: int, raw_text: str) -> bool:
    with db_connection() as conn:
        cursor = conn.execute(
            "UPDATE entries SET raw_text = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (raw_text, entry_id)
        )
        conn.commit()
        updated = cursor.rowcount > 0
    return updated


def delete_entry(entry_id: int) -> dict | None:
    with db_connection() as conn:
        row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
        if row:
            conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
            conn.commit()
    return dict(row) if row else None


def create_event(date: str, event_type: str, title: str, source_date: str) -> int:
    with db_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO events (date, type, title, source_date) VALUES (?, ?, ?, ?)",
            (date, event_type, title, source_date)
        )
        event_id = cursor.lastrowid
        conn.commit()
    return event_id


def get_events_by_date(date: str) -> list[dict]:
    with db_connection() as conn:
        rows = conn.execute(
            "SELECT id, date, type, title, source_date FROM events WHERE date = ?",
            (date,)
        ).fetchall()
    return [dict(row) for row in rows]


def get_upcoming_todos() -> list[dict]:
    import datetime
    today = datetime.date.today().isoformat()
    with db_connection() as conn:
        rows = conn.execute(
            "SELECT id, date, title, source_date FROM events WHERE type = 'todo' AND date >= ? ORDER BY date",
            (today,)
        ).fetchall()
    return [dict(row) for row in rows]


def delete_events_by_source_date(source_date: str):
    with db_connection() as conn:
        conn.execute("DELETE FROM events WHERE source_date = ?", (source_date,))
        conn.commit()

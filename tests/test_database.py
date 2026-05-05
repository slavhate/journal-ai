import sqlite3
import pytest

from backend.database import (
    init_db, get_db_path, create_entry, get_entries_by_date,
    update_entry, delete_entry, create_event, get_events_by_date
)


def test_init_db_creates_tables():
    init_db()
    conn = sqlite3.connect(get_db_path())
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    assert "entries" in tables
    assert "events" in tables


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

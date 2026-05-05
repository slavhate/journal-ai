import re
import logging
from typing import Literal
from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel, field_validator
from datetime import date

logger = logging.getLogger(__name__)

from backend.database import (
    create_entry, get_entries_by_date, update_entry, update_entry_formatted_md,
    delete_entry, get_entry_by_id, create_event, delete_events_by_source_date
)
from backend.ollama_service import format_entry, generate_embedding
from backend.markdown_service import read_md_file, write_md_file, rebuild_md_file
from backend.chromadb_service import upsert_document

router = APIRouter(prefix="/api/entries", tags=["entries"])

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class EntryCreate(BaseModel):
    category: Literal["work", "personal", "finance"]
    raw_text: str

    @field_validator("raw_text")
    @classmethod
    def raw_text_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("raw_text must not be empty")
        if len(v) > 2000:
            raise ValueError("raw_text must not exceed 2000 characters")
        return v


class EntryUpdate(BaseModel):
    raw_text: str

    @field_validator("raw_text")
    @classmethod
    def raw_text_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("raw_text must not be empty")
        if len(v) > 2000:
            raise ValueError("raw_text must not exceed 2000 characters")
        return v


@router.post("")
async def create_entry_endpoint(entry: EntryCreate):
    today = date.today().isoformat()

    entry_id = create_entry(today, entry.category, entry.raw_text)

    existing_md = read_md_file(today)
    result = await format_entry(entry.raw_text, entry.category, existing_md)
    formatted_md = result["markdown"]

    update_entry_formatted_md(entry_id, formatted_md)

    if existing_md:
        category_header = f"## {entry.category.capitalize()}"
        if category_header in existing_md:
            insert_pos = existing_md.find(category_header) + len(category_header)
            next_section = existing_md.find("\n## ", insert_pos)
            if next_section == -1:
                new_md = existing_md.rstrip() + "\n" + formatted_md + "\n"
            else:
                new_md = (
                    existing_md[:next_section].rstrip() + "\n" + formatted_md + "\n" +
                    existing_md[next_section:]
                )
        else:
            new_md = existing_md.rstrip() + f"\n\n## {entry.category.capitalize()}\n{formatted_md}\n"
    else:
        new_md = f"# {today}\n\n## {entry.category.capitalize()}\n{formatted_md}\n"

    try:
        write_md_file(today, new_md)
    except Exception as exc:
        logger.warning("Failed to write md file for %s: %s", today, exc)

    for event in result.get("events", []):
        try:
            create_event(event["date"], event["type"], event["title"], today)
        except (KeyError, TypeError) as exc:
            logger.warning("Skipping malformed event from AI: %s — %s", event, exc)

    try:
        full_md = read_md_file(today)
        embedding = await generate_embedding(full_md)
        if embedding:
            all_entries = get_entries_by_date(today)
            categories = list(set(e["category"] for e in all_entries))
            upsert_document(today, full_md, embedding, categories)
    except Exception as exc:
        logger.warning("ChromaDB upsert failed for %s: %s", today, exc)

    return {"id": entry_id, "category": entry.category, "raw_text": entry.raw_text, "formatted_md": formatted_md}


@router.put("/{entry_id}")
async def update_entry_endpoint(entry_id: int, entry: EntryUpdate):
    updated = update_entry(entry_id, entry.raw_text)
    if not updated:
        raise HTTPException(status_code=404, detail="Entry not found")

    row = get_entry_by_id(entry_id)
    if not row:
        raise HTTPException(status_code=404, detail="Entry not found")

    entry_date = row["date"]
    all_entries = get_entries_by_date(entry_date)

    sections = {"work": [], "personal": [], "finance": []}
    for e in all_entries:
        fmt = await format_entry(e["raw_text"], e["category"], "")
        sections[e["category"]].append(fmt["markdown"])
        update_entry_formatted_md(e["id"], fmt["markdown"])

    new_md = rebuild_md_file(entry_date, sections)
    try:
        write_md_file(entry_date, new_md)
    except Exception as exc:
        logger.warning("Failed to write md file for %s: %s", entry_date, exc)

    delete_events_by_source_date(entry_date)
    for e in all_entries:
        fmt = await format_entry(e["raw_text"], e["category"], "")
        for event in fmt.get("events", []):
            try:
                create_event(event["date"], event["type"], event["title"], entry_date)
            except (KeyError, TypeError) as exc:
                logger.warning("Skipping malformed event from AI: %s — %s", event, exc)

    try:
        embedding = await generate_embedding(new_md)
        if embedding:
            categories = list(set(e["category"] for e in all_entries))
            upsert_document(entry_date, new_md, embedding, categories)
    except Exception as exc:
        logger.warning("ChromaDB upsert failed for %s: %s", entry_date, exc)

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
            fmt = await format_entry(e["raw_text"], e["category"], "")
            sections[e["category"]].append(fmt["markdown"])
        new_md = rebuild_md_file(entry_date, sections)
    else:
        new_md = ""

    try:
        write_md_file(entry_date, new_md)
    except Exception as exc:
        logger.warning("Failed to write md file for %s: %s", entry_date, exc)

    if new_md:
        try:
            embedding = await generate_embedding(new_md)
            if embedding:
                categories = list(set(e["category"] for e in all_entries))
                upsert_document(entry_date, new_md, embedding, categories)
        except Exception as exc:
            logger.warning("ChromaDB upsert failed for %s: %s", entry_date, exc)

    return {"status": "deleted", "id": entry_id}


@router.get("/{date}")
async def get_entries_endpoint(date: str = Path(..., pattern=r"^\d{4}-\d{2}-\d{2}$")):
    entries = get_entries_by_date(date)
    grouped = {"work": [], "personal": [], "finance": []}
    for e in entries:
        grouped[e["category"]].append({
            "id": e["id"],
            "raw_text": e["raw_text"],
            "formatted_md": e.get("formatted_md") or e["raw_text"],
            "created_at": e["created_at"]
        })
    return grouped

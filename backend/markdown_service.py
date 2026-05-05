import os
import re
from backend.config import ENTRIES_DIR

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _safe_date(date: str) -> str:
    if not _DATE_RE.match(date):
        raise ValueError(f"Invalid date format: {date!r}")
    return date


def read_md_file(date: str) -> str:
    path = os.path.join(ENTRIES_DIR, f"{_safe_date(date)}.md")
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_md_file(date: str, content: str):
    os.makedirs(ENTRIES_DIR, exist_ok=True)
    path = os.path.join(ENTRIES_DIR, f"{_safe_date(date)}.md")
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

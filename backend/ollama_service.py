import json
import httpx
from backend.config import OLLAMA_BASE_URL, FORMATTING_MODEL, EMBEDDING_MODEL


FORMATTING_PROMPT = """You are a journal entry formatter. Given a raw text entry and its category, do two things:

1. Format the entry as a markdown sub-section. Create a short ### sub-heading based on the topic. Then write one or more bullet points that capture the meaning of the entry.
   - Each bullet point must be a complete, meaningful phrase — never empty, never just punctuation like a comma.
   - If the entry is a simple one-liner (e.g. "got a haircut"), use the sub-heading as the topic and write the bullet as a brief factual statement (e.g. "- Haircut done").
   - For Finance entries: always use Indian Rupee (₹) as the default currency symbol for any monetary amounts, unless a different currency is explicitly mentioned.

2. Extract any future events, todos, or birthdays mentioned in the text.

Respond ONLY with valid JSON in this exact format:
{
  "markdown": "### Sub-heading\\n- Bullet point content",
  "events": [{"date": "YYYY-MM-DD", "type": "todo|birthday|event", "title": "short description"}]
}

If no events found, return empty events array. The markdown must NOT include the ## Category heading. Every bullet point must contain actual text."""


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

    try:
        response = await call_ollama(prompt, system=FORMATTING_PROMPT)
        raw_response = response.get("response", "{}")
    except Exception:
        return {"markdown": f"### Note\n- {raw_text}", "events": []}

    try:
        result = json.loads(raw_response)
    except json.JSONDecodeError:
        result = {"markdown": f"### Note\n- {raw_text}", "events": []}

    if not isinstance(result, dict):
        result = {}
    if not isinstance(result.get("markdown"), str):
        result["markdown"] = f"### Note\n- {raw_text}"
    if not isinstance(result.get("events"), list):
        result["events"] = []

    # Strip bullets that are empty or contain only punctuation/whitespace
    cleaned_lines = []
    for line in result["markdown"].split("\n"):
        if line.startswith("- "):
            content = line[2:].strip().strip(".,;:")
            if not content:
                continue
        cleaned_lines.append(line)

    # If all bullets were stripped, fall back to raw text as the bullet
    md = "\n".join(cleaned_lines)
    if "\n- " not in md and not md.endswith("\n- "):
        first_line = md.split("\n")[0] if md else f"### {raw_text.capitalize()}"
        md = f"{first_line}\n- {raw_text}"

    result["markdown"] = md
    return result


async def generate_embedding(text: str) -> list[float]:
    try:
        response = await call_ollama_embedding(text)
        embedding = response.get("embedding", [])
        return embedding if isinstance(embedding, list) else []
    except Exception:
        return []

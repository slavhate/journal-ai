from fastapi import APIRouter
import httpx
from backend.config import OLLAMA_BASE_URL, FORMATTING_MODEL, EMBEDDING_MODEL

router = APIRouter(tags=["health"])


@router.get("/api/health")
async def health():
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            resp.raise_for_status()
            models = [m["name"] for m in resp.json().get("models", [])]
    except Exception:
        return {"status": "offline", "models": []}

    has_formatting = any(FORMATTING_MODEL in m for m in models)
    has_embedding = any(EMBEDDING_MODEL in m for m in models)

    return {
        "status": "ready" if (has_formatting and has_embedding) else "partial",
        "formatting_model": {"name": FORMATTING_MODEL, "available": has_formatting},
        "embedding_model": {"name": EMBEDDING_MODEL, "available": has_embedding},
    }

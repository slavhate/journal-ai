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
async def test_format_entry_handles_invalid_json():
    mock_response = {"response": "not valid json"}
    with patch("backend.ollama_service.call_ollama", new_callable=AsyncMock, return_value=mock_response):
        result = await format_entry("some text", "work", "")
        assert "markdown" in result
        assert "events" in result


@pytest.mark.asyncio
async def test_generate_embedding_returns_list():
    mock_response = {"embedding": [0.1, 0.2, 0.3]}
    with patch("backend.ollama_service.call_ollama_embedding", new_callable=AsyncMock, return_value=mock_response):
        result = await generate_embedding("some text")
        assert isinstance(result, list)
        assert len(result) > 0

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

        count = self.collection.count()
        if count > 0:
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=min(5, count),
                include=["documents", "metadatas", "distances"]
            )
        else:
            results = {"documents": [[]], "metadatas": [[]], "distances": [[]]}

        date_files = self._extract_date_files(query)

        documents = []

        for date_str in date_files:
            content = self._read_md_file(date_str)
            if content and content not in documents:
                documents.append(content)

        if results["documents"] and results["documents"][0]:
            for doc in results["documents"][0]:
                if doc and doc not in documents:
                    documents.append(doc)

        if not documents:
            return "No matching journal entries found."

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

        iso_matches = re.findall(r"\d{4}-\d{2}-\d{2}", query)
        dates.extend(iso_matches)

        lower = query.lower()
        if "yesterday" in lower:
            dates.append((today - timedelta(days=1)).strftime("%Y-%m-%d"))
        if "today" in lower:
            dates.append(today.strftime("%Y-%m-%d"))
        if "last week" in lower:
            for i in range(7, 14):
                dates.append((today - timedelta(days=i)).strftime("%Y-%m-%d"))

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

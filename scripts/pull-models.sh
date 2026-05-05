#!/usr/bin/env bash
set -e

OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://ollama:11434}"

echo "Waiting for Ollama to be ready..."
until curl -sf "${OLLAMA_BASE_URL}/api/tags" > /dev/null 2>&1; do
    echo "Ollama not ready yet, retrying in 5 seconds..."
    sleep 5
done

echo "Ollama is ready. Pulling models..."

echo "Pulling llama3.2:3b..."
curl -sf -X POST "${OLLAMA_BASE_URL}/api/pull" \
    -H "Content-Type: application/json" \
    -d '{"name": "llama3.2:3b"}' | tail -1

echo "Pulling nomic-embed-text..."
curl -sf -X POST "${OLLAMA_BASE_URL}/api/pull" \
    -H "Content-Type: application/json" \
    -d '{"name": "nomic-embed-text"}' | tail -1

echo "All models pulled successfully."

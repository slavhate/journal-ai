import os

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
DATA_DIR = os.getenv("DATA_DIR", "/data")
FORMATTING_MODEL = os.getenv("FORMATTING_MODEL", "llama3.2:3b")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
APP_PORT = int(os.getenv("APP_PORT", "8550"))
FRONTEND_DIR = os.getenv("FRONTEND_DIR", "/app/frontend")

ENTRIES_DIR = os.path.join(DATA_DIR, "entries")
DB_DIR = os.path.join(DATA_DIR, "db")
SQLITE_PATH = os.path.join(DB_DIR, "journal.db")
CHROMADB_PATH = os.path.join(DB_DIR, "chromadb")

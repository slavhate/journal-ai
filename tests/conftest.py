import os
import tempfile

# Set env vars before any backend module is imported
_tmp = tempfile.mkdtemp()
os.environ.setdefault("DATA_DIR", _tmp)
os.environ["FRONTEND_DIR"] = os.path.join(os.path.dirname(__file__), "..", "frontend")

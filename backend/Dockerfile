# --- builder: install deps and strip bloat ---
FROM python:3.13-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ && \
    rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --prefix=/deps -r requirements.txt && \
    find /deps -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; true && \
    find /deps -type d -name "tests"       -exec rm -rf {} + 2>/dev/null; true && \
    find /deps -type d -name "test"        -exec rm -rf {} + 2>/dev/null; true && \
    find /deps -name "*.pyc"               -delete 2>/dev/null; true

# --- final: clean runtime image ---
FROM python:3.13-slim

WORKDIR /app

COPY --from=builder /deps /usr/local
COPY backend/  /app/backend/
COPY frontend/ /app/frontend/

RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8550

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8550"]

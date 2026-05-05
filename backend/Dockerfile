FROM python:3.13-slim

WORKDIR /app

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ /app/backend/
COPY frontend/ /app/frontend/

RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8550

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8550"]

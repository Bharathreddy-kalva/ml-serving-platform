# Build context must be the repo root so ml/ scripts are available for retraining.
# docker compose passes `context: ..` from infra/, which resolves to the repo root.

FROM python:3.11-slim

WORKDIR /repo

RUN apt-get update && apt-get install -y --no-install-recommends \
      gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps (cached layer — only busted when requirements.txt changes)
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy source in the same relative layout as the local checkout so that
# Path(__file__).parent.parent.parent resolves to /repo (≡ repo root locally)
COPY backend/ backend/
COPY ml/ ml/

WORKDIR /repo/backend

EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=5s --retries=10 --start-period=30s \
  CMD curl -sf http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

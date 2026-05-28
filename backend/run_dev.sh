#!/usr/bin/env bash
# Start the FastAPI backend for local development (no Docker, no PostgreSQL).
# Run from the repo root: bash backend/run_dev.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$REPO_ROOT/.venv"
PYTHON="$VENV/bin/python"
BACKEND_DIR="$REPO_ROOT/backend"
MLFLOW_DB="$REPO_ROOT/ml/artifacts/mlflow_backend/mlflow.db"

# ── Preflight checks ──────────────────────────────────────────────────────────
if [[ ! -x "$PYTHON" ]]; then
  echo "ERROR: .venv not found. Run: bash ml/setup.sh" >&2
  exit 1
fi

if [[ ! -f "$MLFLOW_DB" ]]; then
  echo "ERROR: MLflow database not found at $MLFLOW_DB"
  echo "       Run 'bash run_local.sh' first to train and register a model."
  exit 1
fi

# ── Install/sync backend dependencies ────────────────────────────────────────
echo "Syncing backend dependencies ..."
"$VENV/bin/pip" install --quiet -r "$BACKEND_DIR/requirements.txt"

# ── Environment ───────────────────────────────────────────────────────────────
# Use the local SQLite MLflow store directly — no tracking server needed
export MLFLOW_TRACKING_URI="sqlite:///$MLFLOW_DB"
export BACKEND_CORS_ORIGINS='["http://localhost:3000"]'

echo ""
echo "  MLflow store : $MLFLOW_TRACKING_URI"
echo "  API          : http://localhost:8000"
echo "  Swagger docs : http://localhost:8000/docs"
echo ""

# ── Start uvicorn ─────────────────────────────────────────────────────────────
cd "$BACKEND_DIR"
exec "$VENV/bin/uvicorn" app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload \
  --reload-dir "$BACKEND_DIR/app"

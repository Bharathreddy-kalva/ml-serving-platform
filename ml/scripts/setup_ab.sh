#!/usr/bin/env bash
# Set up A/B testing: train GradientBoosting v2, then promote stages.
# Run from repo root: bash ml/scripts/setup_ab.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV="$REPO_ROOT/.venv"
MLFLOW_DB="$REPO_ROOT/ml/artifacts/mlflow_backend/mlflow.db"

log() { echo "[setup_ab] $*"; }
hr()  { echo "────────────────────────────────────────────────────────"; }

# ── Preflight ─────────────────────────────────────────────────────────────────
[[ -x "$VENV/bin/python" ]] || { log "ERROR: run 'bash ml/setup.sh' first"; exit 1; }
[[ -f "$MLFLOW_DB" ]]       || { log "ERROR: run 'bash run_local.sh' first to create v1"; exit 1; }

export MLFLOW_TRACKING_URI="sqlite:///$MLFLOW_DB"

cd "$REPO_ROOT"

# ── Train v2 (GradientBoosting) ───────────────────────────────────────────────
hr
log "Step 1/2 — Training v2 (GradientBoostingClassifier)..."
"$VENV/bin/python" ml/scripts/train.py \
  --config ml/configs/gradientboosting.yaml \
  --model-name iris-classifier

# ── Promote stages ────────────────────────────────────────────────────────────
hr
log "Step 2/2 — Promoting: v1 → Staging, v2 → Production..."
"$VENV/bin/python" ml/scripts/promote_ab.py

hr
log "Done. Restart the backend to load both versions:"
log "  bash backend/run_dev.sh"

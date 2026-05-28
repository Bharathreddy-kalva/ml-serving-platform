#!/usr/bin/env bash
# End-to-end local ML pipeline runner (no Docker required).
#
# What it does:
#   1. Checks / creates the venv
#   2. Starts an MLflow tracking server on http://localhost:5000
#   3. Trains the iris-classifier and registers it in MLflow
#   4. Confirms the registered model version exists
#   5. Shuts down the MLflow server on exit
#
# Usage (from repo root):
#   bash run_local.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$REPO_ROOT/.venv"
PYTHON="$VENV/bin/python"
MLFLOW_PORT=5000
MLFLOW_TRACKING_URI="http://localhost:$MLFLOW_PORT"
MLFLOW_BACKEND="$REPO_ROOT/ml/artifacts/mlflow_backend"   # SQLite
MLFLOW_ARTIFACT_ROOT="$REPO_ROOT/ml/artifacts/mlruns"
MLFLOW_PID_FILE="/tmp/mlserving_mlflow.pid"

# ── Helpers ───────────────────────────────────────────────────────────────────
log()  { echo "[run_local] $*"; }
die()  { echo "[run_local] ERROR: $*" >&2; exit 1; }
hr()   { echo "────────────────────────────────────────────────────────"; }

cleanup() {
  if [[ -f "$MLFLOW_PID_FILE" ]]; then
    local pid
    pid=$(cat "$MLFLOW_PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
      log "Stopping MLflow server (PID $pid) ..."
      kill "$pid"
    fi
    rm -f "$MLFLOW_PID_FILE"
  fi
}
trap cleanup EXIT

# ── Step 1: Ensure venv exists ────────────────────────────────────────────────
hr
log "Step 1/4 — Virtual environment"

if [[ ! -x "$PYTHON" ]]; then
  log "venv not found — running ml/setup.sh ..."
  bash "$REPO_ROOT/ml/setup.sh"
else
  log "venv found at $VENV"
fi

# ── Step 2: Start MLflow tracking server ──────────────────────────────────────
hr
log "Step 2/4 — Starting MLflow tracking server on port $MLFLOW_PORT"

mkdir -p "$MLFLOW_BACKEND" "$MLFLOW_ARTIFACT_ROOT"

# Kill any stale server on that port
if lsof -ti tcp:"$MLFLOW_PORT" &>/dev/null; then
  log "Port $MLFLOW_PORT already in use — attempting to kill existing process ..."
  lsof -ti tcp:"$MLFLOW_PORT" | xargs kill -9 2>/dev/null || true
  sleep 1
fi

"$VENV/bin/mlflow" server \
  --backend-store-uri "sqlite:///$MLFLOW_BACKEND/mlflow.db" \
  --default-artifact-root "$MLFLOW_ARTIFACT_ROOT" \
  --host 127.0.0.1 \
  --port "$MLFLOW_PORT" \
  &>/tmp/mlserving_mlflow.log &
echo $! > "$MLFLOW_PID_FILE"
log "MLflow PID: $(cat "$MLFLOW_PID_FILE")"

# Wait until the server is accepting connections (up to 20 s)
log "Waiting for MLflow to be ready ..."
for i in $(seq 1 20); do
  if curl -sf "$MLFLOW_TRACKING_URI/health" &>/dev/null; then
    log "MLflow ready after ${i}s"
    break
  fi
  if [[ $i -eq 20 ]]; then
    die "MLflow did not start in time. Check /tmp/mlserving_mlflow.log"
  fi
  sleep 1
done

log "MLflow UI → $MLFLOW_TRACKING_URI"

# ── Step 3: Train and register the model ──────────────────────────────────────
hr
log "Step 3/4 — Training iris-classifier"

cd "$REPO_ROOT"
MLFLOW_TRACKING_URI="$MLFLOW_TRACKING_URI" \
  "$PYTHON" ml/scripts/train.py \
    --config ml/configs/default.yaml \
    --model-name iris-classifier

# ── Step 4: Confirm registration ──────────────────────────────────────────────
hr
log "Step 4/4 — Confirming model registration"

"$PYTHON" - <<'PYEOF'
import sys
import mlflow
from mlflow.tracking import MlflowClient

import os
uri = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")
mlflow.set_tracking_uri(uri)
client = MlflowClient()

try:
    versions = client.search_model_versions("name='iris-classifier'")
except Exception as e:
    print(f"ERROR querying registry: {e}", file=sys.stderr)
    sys.exit(1)

if not versions:
    print("ERROR: no versions found for 'iris-classifier'", file=sys.stderr)
    sys.exit(1)

latest = sorted(versions, key=lambda v: int(v.version))[-1]
print(f"  Model name  : {latest.name}")
print(f"  Version     : {latest.version}")
print(f"  Stage       : {latest.current_stage}")
print(f"  Run ID      : {latest.run_id}")
print(f"  Source      : {latest.source}")
print("\nAll registered versions:")
for v in versions:
    print(f"  v{v.version}  stage={v.current_stage}  run={v.run_id[:8]}...")
PYEOF

hr
log "Done. Open the MLflow UI at $MLFLOW_TRACKING_URI"
log "The server will stop when this script exits (Ctrl-C)."
log "To keep it running: nohup bash run_local.sh &"

# Keep running so the MLflow server stays alive for manual inspection
wait

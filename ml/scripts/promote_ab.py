"""Promote iris-classifier for A/B testing:
  lowest version  → Staging   (v1 — RandomForest, challenger)
  highest version → Production (v2 — GradientBoosting, champion)
"""

import os
import sys
from pathlib import Path

import mlflow
from mlflow.tracking import MlflowClient

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DB_URI = os.environ.get(
    "MLFLOW_TRACKING_URI",
    f"sqlite:///{REPO_ROOT}/ml/artifacts/mlflow_backend/mlflow.db",
)

mlflow.set_tracking_uri(DB_URI)
client = MlflowClient()

versions = sorted(
    client.search_model_versions("name='iris-classifier'"),
    key=lambda v: int(v.version),
)

if len(versions) < 2:
    print(f"ERROR: need at least 2 versions, found {len(versions)}.", file=sys.stderr)
    print("       Run 'bash ml/scripts/setup_ab.sh' to train v2 first.", file=sys.stderr)
    sys.exit(1)

v1, v2 = versions[0], versions[-1]

client.transition_model_version_stage(
    "iris-classifier", v1.version, "Staging", archive_existing_versions=False
)
client.transition_model_version_stage(
    "iris-classifier", v2.version, "Production", archive_existing_versions=False
)

print(f"\n  v{v1.version} (RF)  → Staging")
print(f"  v{v2.version} (GB)  → Production\n")

print("Current registry state:")
for mv in sorted(client.search_model_versions("name='iris-classifier'"), key=lambda v: int(v.version)):
    print(f"  v{mv.version}  stage={mv.current_stage:12s}  run={mv.run_id[:8]}…")

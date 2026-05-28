"""Auto-retraining subsystem.

Responsibilities
────────────────
1. drift_check_job()   — called every N seconds by APScheduler; checks drift for all
                         loaded models; triggers a retrain when PSI > 0.2 is found and
                         the cooldown has elapsed.
2. trigger_retrain()   — entry point for both auto and manual retrains; runs
                         ml/scripts/train.py in a thread-pool executor so it doesn't
                         block the event loop; persists events to retrain_log.json.
3. read_log() / helpers — log file I/O.
"""

import asyncio
import json
import logging
import os
import re
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Literal

from app.config import settings
from app.schemas.retrain import RetrainEvent

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_LOG_FILE   = _REPO_ROOT / "ml/artifacts/retrain_log.json"
_MAX_EVENTS = 100

# ── Runtime state (single-process; fine with asyncio's cooperative threading) ─
_retrain_in_progress: bool = False
_last_retrain: dict[str, datetime] = {}   # model_name → last retrain wall-time


# ── Log file helpers ──────────────────────────────────────────────────────────

def read_log(limit: int = 10) -> list[dict]:
    if not _LOG_FILE.exists():
        return []
    try:
        events = json.loads(_LOG_FILE.read_text())
        return events[:limit]
    except Exception:
        return []


def _append_log(event: dict) -> None:
    try:
        existing = json.loads(_LOG_FILE.read_text()) if _LOG_FILE.exists() else []
    except Exception:
        existing = []
    existing.insert(0, event)          # newest first
    existing = existing[:_MAX_EVENTS]
    _LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    _LOG_FILE.write_text(json.dumps(existing, indent=2, default=str))


# ── State helpers ─────────────────────────────────────────────────────────────

def is_retrain_running() -> bool:
    return _retrain_in_progress


def _should_auto_retrain(model_name: str) -> bool:
    if _retrain_in_progress:
        return False
    last = _last_retrain.get(model_name)
    if last is None:
        return True
    elapsed = (datetime.utcnow() - last).total_seconds()
    return elapsed >= settings.retrain_cooldown_seconds


# ── Subprocess helpers ────────────────────────────────────────────────────────

def _extract_new_version(stdout: str, stderr: str = "") -> str | None:
    # MLflow emits "Created version 'N'" to stderr; fall back to stdout just in case
    for text in (stderr, stdout):
        match = re.search(r"Created version '(\d+)'", text)
        if match:
            return match.group(1)
    return None


def _run_subprocess(model_name: str) -> subprocess.CompletedProcess:
    """Blocking — must be called inside run_in_executor."""
    env = {**os.environ, "MLFLOW_TRACKING_URI": settings.mlflow_tracking_uri}
    return subprocess.run(
        [
            sys.executable,
            "ml/scripts/train.py",
            "--config", settings.retrain_config,
            "--model-name", model_name,
        ],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=300,
        env=env,
    )


# ── Main entry point ──────────────────────────────────────────────────────────

async def trigger_retrain(
    model_name: str,
    triggered_by_version: str,
    trigger: Literal["auto", "manual"],
    reason: str,
) -> RetrainEvent:
    """Run training subprocess and persist the event. Raises on timeout."""
    global _retrain_in_progress, _last_retrain
    _retrain_in_progress = True
    event_id = str(uuid.uuid4())
    started_at = datetime.utcnow()

    try:
        loop = asyncio.get_event_loop()
        proc = await loop.run_in_executor(None, _run_subprocess, model_name)
        duration = (datetime.utcnow() - started_at).total_seconds()

        if proc.returncode == 0:
            new_version = _extract_new_version(proc.stdout, proc.stderr)
            status: Literal["success", "failed"] = "success"
            error = None
            logger.info(
                "[retrainer] %s retrain OK — new version %s (%.1fs)",
                model_name, new_version, duration,
            )
        else:
            new_version = None
            status = "failed"
            error = (proc.stderr or "")[-500:].strip() or "Non-zero exit"
            logger.error(
                "[retrainer] %s retrain FAILED after %.1fs: %s",
                model_name, duration, error[:120],
            )

    except subprocess.TimeoutExpired:
        duration = (datetime.utcnow() - started_at).total_seconds()
        new_version = None
        status = "failed"
        error = "Subprocess timed out after 300 s"
        logger.error("[retrainer] %s retrain timed out", model_name)

    finally:
        _retrain_in_progress = False

    _last_retrain[model_name] = datetime.utcnow()

    event = RetrainEvent(
        id=event_id,
        timestamp=started_at,
        model_name=model_name,
        triggered_by_version=triggered_by_version,
        trigger=trigger,
        reason=reason,
        config=settings.retrain_config,
        status=status,
        new_version=new_version,
        duration_seconds=round(duration, 1),
        error=error,
    )
    _append_log(event.model_dump())
    return event


# ── APScheduler job ───────────────────────────────────────────────────────────

async def drift_check_job() -> None:
    """Scheduled every `retrain_check_interval` seconds.
    Checks drift for all loaded model versions; triggers retraining on the
    first drifted model whose cooldown has elapsed.
    """
    # Import here to avoid circular imports at module load time
    from app.utils.drift import compute_drift_report
    from app.utils.model_loader import ModelRegistry

    if _retrain_in_progress:
        logger.debug("[scheduler] Skipping drift check — retrain in progress")
        return

    checked_names: set[str] = set()
    for info in ModelRegistry.list_loaded():
        if info.name in checked_names:
            continue
        checked_names.add(info.name)

        if not _should_auto_retrain(info.name):
            continue

        # Check the Staging (lowest) version — that's where simulate_drift sends data
        ab_versions = ModelRegistry.get_ab_versions(info.name)
        check_version = ab_versions[0] if ab_versions else info.version

        try:
            report = await compute_drift_report(info.name, check_version, None)
        except Exception as exc:
            logger.error("[scheduler] Drift check error for %s: %s", info.name, exc)
            continue

        if report.drifted_features == 0:
            logger.debug("[scheduler] No drift for %s v%s", info.name, check_version)
            continue

        max_psi = max((f.psi for f in report.features if f.drifted), default=0.0)
        reason = (
            f"{report.drifted_features}/{len(report.features)} features drifted "
            f"(max PSI={max_psi:.4f})"
        )
        logger.info(
            "[scheduler] Drift detected on %s v%s — %s. Triggering auto-retrain.",
            info.name, check_version, reason,
        )
        await trigger_retrain(info.name, check_version, "auto", reason)
        # Retrain one model per tick to keep things predictable
        return

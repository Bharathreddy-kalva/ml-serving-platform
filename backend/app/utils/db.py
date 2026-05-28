"""Prediction store.

Uses PostgreSQL (asyncpg) when DATABASE_URL points to a reachable PostgreSQL
instance.  Falls back to an in-memory deque so local development works without
Docker.

Public API (unchanged regardless of backend):
  init_db(database_url)            — call once on startup
  close_db()                       — call on shutdown
  log_prediction(...)              — write one prediction row
  fetch_predictions(...)           — read rows for (model, version)
  fetch_predictions_for_model(...) — read all rows for a model
"""

import json
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import date, datetime

logger = logging.getLogger(__name__)

# ── Shared data transfer object ───────────────────────────────────────────────

@dataclass
class _Row:
    model_name: str
    model_version: str
    features: list
    predictions: list
    latency_ms: float
    ground_truth: list | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)


# ── Runtime state ─────────────────────────────────────────────────────────────

_pool = None                              # asyncpg.Pool — None means in-memory mode
_store: deque[_Row] = deque(maxlen=10_000)  # in-memory fallback


# ── Lifecycle ─────────────────────────────────────────────────────────────────

async def init_db(database_url: str) -> bool:
    """Try to open an asyncpg connection pool.  Returns True on success."""
    global _pool
    if not database_url or "postgresql" not in database_url:
        logger.info("[db] No PostgreSQL URL configured — using in-memory store")
        return False
    try:
        import asyncpg
        _pool = await asyncpg.create_pool(
            database_url,
            min_size=1,
            max_size=10,
            command_timeout=10,
        )
        async with _pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        logger.info("[db] Connected to PostgreSQL")
        return True
    except Exception as exc:
        logger.warning("[db] PostgreSQL unavailable (%s) — falling back to in-memory store", exc)
        _pool = None
        return False


async def close_db() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


# ── Write ─────────────────────────────────────────────────────────────────────

async def log_prediction(
    model_name: str,
    version: str,
    features: list,
    predictions: list,
    latency_ms: float,
    ground_truth: list | None = None,
) -> None:
    if _pool:
        async with _pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO predictions
                  (model_name, model_version, features, predictions, latency_ms, ground_truth)
                VALUES ($1, $2, $3::jsonb, $4::jsonb, $5, $6::jsonb)
                """,
                model_name,
                version,
                json.dumps(features),
                json.dumps(predictions),
                latency_ms,
                json.dumps(ground_truth) if ground_truth is not None else None,
            )
    else:
        _store.append(
            _Row(
                model_name=model_name,
                model_version=version,
                features=features,
                predictions=predictions,
                latency_ms=latency_ms,
                ground_truth=ground_truth,
            )
        )


# ── Read ──────────────────────────────────────────────────────────────────────

def _row_from_record(r) -> _Row:
    return _Row(
        model_name=r["model_name"],
        model_version=r["model_version"],
        features=r["features"] if isinstance(r["features"], list) else json.loads(r["features"]),
        predictions=r["predictions"] if isinstance(r["predictions"], list) else json.loads(r["predictions"]),
        latency_ms=float(r["latency_ms"] or 0),
        ground_truth=r["ground_truth"] if isinstance(r.get("ground_truth"), (list, type(None))) else json.loads(r["ground_truth"]) if r["ground_truth"] else None,
        created_at=r["created_at"] if isinstance(r["created_at"], datetime) else datetime.fromisoformat(str(r["created_at"])),
    )


async def fetch_predictions(
    model_name: str,
    version: str,
    since: date | None = None,
) -> list[_Row]:
    if _pool:
        async with _pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT model_name, model_version, features, predictions,
                       latency_ms, ground_truth, created_at
                FROM predictions
                WHERE model_name = $1
                  AND model_version = $2
                  AND ($3::date IS NULL OR created_at::date >= $3::date)
                ORDER BY created_at
                """,
                model_name,
                version,
                since,
            )
        return [_row_from_record(r) for r in rows]
    else:
        return [
            r for r in _store
            if r.model_name == model_name
            and r.model_version == version
            and (since is None or r.created_at.date() >= since)
        ]


async def fetch_predictions_for_model(
    model_name: str,
    since: date | None = None,
) -> list[_Row]:
    """All predictions for a model across every version (used by A/B stats)."""
    if _pool:
        async with _pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT model_name, model_version, features, predictions,
                       latency_ms, ground_truth, created_at
                FROM predictions
                WHERE model_name = $1
                  AND ($2::date IS NULL OR created_at::date >= $2::date)
                ORDER BY created_at
                """,
                model_name,
                since,
            )
        return [_row_from_record(r) for r in rows]
    else:
        return [
            r for r in _store
            if r.model_name == model_name
            and (since is None or r.created_at.date() >= since)
        ]

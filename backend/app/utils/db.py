"""In-memory prediction store for local development."""

from collections import deque
from dataclasses import dataclass, field
from datetime import date, datetime

_MAX_ROWS = 10_000


@dataclass
class _Row:
    model_name: str
    model_version: str
    features: list
    predictions: list
    latency_ms: float
    ground_truth: list | None = None   # set when caller provides a label
    created_at: datetime = field(default_factory=datetime.utcnow)


_store: deque[_Row] = deque(maxlen=_MAX_ROWS)


async def log_prediction(
    model_name: str,
    version: str,
    features: list,
    predictions: list,
    latency_ms: float,
    ground_truth: list | None = None,
) -> None:
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


async def fetch_predictions(
    model_name: str,
    version: str,
    since: date | None = None,
) -> list[_Row]:
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
    """Return all predictions for a model across every version (for A/B stats)."""
    return [
        r for r in _store
        if r.model_name == model_name
        and (since is None or r.created_at.date() >= since)
    ]

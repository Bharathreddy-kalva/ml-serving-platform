from fastapi import APIRouter

from app.config import settings
from app.schemas.ab_test import ABTestStats, VersionStats
from app.utils.db import fetch_predictions_for_model
from app.utils.model_loader import ModelRegistry

router = APIRouter(prefix="/ab-stats", tags=["a/b testing"])


@router.get("/{model_name}", response_model=ABTestStats)
async def get_ab_stats(model_name: str):
    rows = await fetch_predictions_for_model(model_name)
    total = len(rows)

    # Group rows by version
    by_version: dict[str, list] = {}
    for r in rows:
        by_version.setdefault(r.model_version, []).append(r)

    version_stats: list[VersionStats] = []
    for ver in sorted(by_version, key=lambda v: int(v) if v.isdigit() else 0):
        vrows = by_version[ver]
        labeled = [r for r in vrows if r.ground_truth is not None]
        correct = sum(
            1 for r in labeled
            if r.ground_truth and r.predictions and r.ground_truth[0] == r.predictions[0]
        )
        info = ModelRegistry.get_info(model_name, ver)
        version_stats.append(
            VersionStats(
                version=ver,
                stage=info.stage if info else "Unknown",
                count=len(vrows),
                traffic_pct=round(len(vrows) / total * 100, 1) if total else 0.0,
                avg_latency_ms=round(sum(r.latency_ms for r in vrows) / len(vrows), 2),
                labeled_count=len(labeled),
                accuracy=round(correct / len(labeled), 4) if labeled else None,
            )
        )

    # Include versions that are loaded but have no predictions yet
    for ver in ModelRegistry.get_ab_versions(model_name):
        if ver not in by_version:
            info = ModelRegistry.get_info(model_name, ver)
            version_stats.append(
                VersionStats(
                    version=ver,
                    stage=info.stage if info else "Unknown",
                    count=0,
                    traffic_pct=0.0,
                    avg_latency_ms=0.0,
                    labeled_count=0,
                    accuracy=None,
                )
            )

    version_stats.sort(key=lambda s: int(s.version) if s.version.isdigit() else 0)

    return ABTestStats(
        model_name=model_name,
        split_percent=settings.ab_split_percent,
        total_predictions=total,
        versions=version_stats,
    )

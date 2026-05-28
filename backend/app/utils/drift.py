import json
from datetime import date
from pathlib import Path

import numpy as np
from scipy import stats

from app.schemas.drift import DriftReport, FeatureDrift
from app.utils.db import fetch_predictions

# Feature stats are written here by the training script
_STATS_FILE = Path(__file__).resolve().parent.parent.parent.parent / "ml/artifacts/feature_stats.json"


def _feature_names(n_features: int) -> list[str]:
    """Return human-readable feature names from the training stats file, falling back to
    generic names if the file doesn't exist or can't be parsed."""
    if _STATS_FILE.exists():
        try:
            raw = json.loads(_STATS_FILE.read_text())
            names = list(raw.keys())[:n_features]
            # "sepal length (cm)" → "sepal_length"
            return [n.lower().replace(" (cm)", "").replace(" ", "_") for n in names]
        except Exception:
            pass
    return [f"feature_{i}" for i in range(n_features)]


def _psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    lo = min(expected.min(), actual.min())
    hi = max(expected.max(), actual.max())
    if lo == hi:
        return 0.0
    breakpoints = np.linspace(lo, hi, bins + 1)
    expected_pct = np.histogram(expected, bins=breakpoints)[0] / len(expected) + 1e-8
    actual_pct   = np.histogram(actual,   bins=breakpoints)[0] / len(actual)   + 1e-8
    return float(np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct)))


async def compute_drift_report(
    model_name: str, version: str, since: date | None
) -> DriftReport:
    rows = await fetch_predictions(model_name, version, since)

    _empty = DriftReport(
        model_name=model_name,
        version=version,
        computed_at=date.today(),
        total_predictions=len(rows),
        drifted_features=0,
        features=[],
    )
    # Need ≥4 rows so each split has ≥2 samples (KS test + PSI histogram)
    if len(rows) < 4:
        return _empty

    all_features = np.array([r.features[0] for r in rows])
    n_features   = all_features.shape[1]
    names        = _feature_names(n_features)

    mid       = len(all_features) // 2
    reference = all_features[:mid]
    current   = all_features[mid:]

    feature_drifts: list[FeatureDrift] = []
    for i in range(n_features):
        ref_col, cur_col = reference[:, i], current[:, i]
        psi_val          = _psi(ref_col, cur_col)
        ks_stat, ks_p    = stats.ks_2samp(ref_col, cur_col)
        feature_drifts.append(
            FeatureDrift(
                feature_name=names[i],
                psi=round(psi_val, 4),
                ks_statistic=round(float(ks_stat), 4),
                ks_p_value=round(float(ks_p), 4),
                drifted=psi_val > 0.2,
            )
        )

    return DriftReport(
        model_name=model_name,
        version=version,
        computed_at=date.today(),
        total_predictions=len(rows),
        drifted_features=sum(f.drifted for f in feature_drifts),
        features=feature_drifts,
    )

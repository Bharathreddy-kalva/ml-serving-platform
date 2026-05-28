from pydantic import BaseModel, ConfigDict


class VersionStats(BaseModel):
    version: str
    stage: str
    count: int
    traffic_pct: float
    avg_latency_ms: float
    labeled_count: int
    accuracy: float | None      # None when no labeled predictions exist yet


class ABTestStats(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_name: str
    split_percent: int
    total_predictions: int
    versions: list[VersionStats]

from datetime import date
from pydantic import BaseModel, ConfigDict


class FeatureDrift(BaseModel):
    feature_name: str
    psi: float
    ks_statistic: float
    ks_p_value: float
    drifted: bool


class DriftReport(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_name: str
    version: str
    computed_at: date
    total_predictions: int
    drifted_features: int
    features: list[FeatureDrift]

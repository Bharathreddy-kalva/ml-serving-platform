from pydantic import BaseModel, ConfigDict, field_validator


class PredictRequest(BaseModel):
    features: list[list[float]]
    label: int | None = None   # optional ground-truth class for accuracy tracking

    @field_validator("features", mode="before")
    @classmethod
    def coerce_1d_to_2d(cls, v):
        """Accept a flat list [f1, f2, ...] and wrap it to [[f1, f2, ...]]."""
        if v and isinstance(v[0], (int, float)):
            return [v]
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"features": [5.1, 3.5, 1.4, 0.2]},
                {"features": [[5.1, 3.5, 1.4, 0.2], [6.7, 3.0, 5.2, 2.3]], "label": 0},
            ]
        }
    }


class PredictResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_name: str
    model_version: str          # always the actual version served, never "latest"
    ab_routed: bool = False     # True when version was chosen by the A/B router
    predictions: list[int | float | str]
    probabilities: list[list[float]] | None = None
    latency_ms: float

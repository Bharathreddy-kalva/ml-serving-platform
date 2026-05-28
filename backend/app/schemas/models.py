from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ModelInfo(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    name: str
    version: str
    stage: str
    registered_at: datetime | None = None
    run_id: str | None = None
    metrics: dict[str, float] = {}


class ModelListResponse(BaseModel):
    models: list[ModelInfo]

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict


class RetrainEvent(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    id: str
    timestamp: datetime
    model_name: str
    triggered_by_version: str
    trigger: Literal["auto", "manual"]
    reason: str
    config: str
    status: Literal["success", "failed"]
    new_version: str | None = None
    duration_seconds: float | None = None
    error: str | None = None


class RetrainLogResponse(BaseModel):
    events: list[RetrainEvent]
    retrain_in_progress: bool

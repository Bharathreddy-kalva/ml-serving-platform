from fastapi import APIRouter, HTTPException

from app.schemas.retrain import RetrainEvent, RetrainLogResponse
from app.utils.model_loader import ModelRegistry
from app.utils.retrainer import is_retrain_running, read_log, trigger_retrain

router = APIRouter(tags=["retraining"])


@router.post("/retrain/{model_name}", response_model=RetrainEvent)
async def manual_retrain(model_name: str, version: str = "latest"):
    """Manually trigger retraining for a model. Blocks until training completes (~5-15 s)."""
    if is_retrain_running():
        raise HTTPException(409, "A retrain is already in progress. Try again shortly.")

    # Resolve "latest" to the actual version for the log
    info = ModelRegistry.get_info(model_name, version)
    resolved_version = info.version if info else version

    event = await trigger_retrain(
        model_name=model_name,
        triggered_by_version=resolved_version,
        trigger="manual",
        reason=f"Manual trigger via dashboard (v{resolved_version})",
    )
    return event


@router.get("/retrain-log", response_model=RetrainLogResponse)
async def get_retrain_log(limit: int = 10):
    """Return the last `limit` retraining events (max 50)."""
    events = read_log(limit=min(limit, 50))
    return RetrainLogResponse(events=events, retrain_in_progress=is_retrain_running())

from fastapi import APIRouter
from app.utils.model_loader import ModelRegistry

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {"status": "ok", "loaded_models": ModelRegistry.list_loaded()}


@router.get("/ready")
async def ready():
    if not ModelRegistry.list_loaded():
        return {"status": "not_ready", "reason": "no models loaded"}, 503
    return {"status": "ready"}

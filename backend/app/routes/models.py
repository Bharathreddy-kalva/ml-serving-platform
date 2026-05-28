from fastapi import APIRouter, HTTPException

from app.schemas.models import ModelInfo, ModelListResponse
from app.utils.model_loader import ModelRegistry

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/", response_model=ModelListResponse)
async def list_models():
    return ModelListResponse(models=ModelRegistry.list_loaded())


@router.get("/{model_name}", response_model=ModelInfo)
async def get_model(model_name: str, version: str = "latest"):
    info = ModelRegistry.get_info(model_name, version)
    if info is None:
        raise HTTPException(404, f"Model '{model_name}' not found")
    return info


@router.post("/reload")
async def reload_models():
    await ModelRegistry.load_production_models()
    return {"reloaded": ModelRegistry.list_loaded()}

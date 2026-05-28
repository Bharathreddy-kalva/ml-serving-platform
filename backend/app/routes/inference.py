import time

from fastapi import APIRouter, HTTPException

from app.schemas.inference import PredictRequest, PredictResponse
from app.utils.ab_router import get_ab_version
from app.utils.db import log_prediction
from app.utils.model_loader import ModelRegistry

router = APIRouter(tags=["inference"])


@router.post("/predict/{model_name}", response_model=PredictResponse)
async def predict(model_name: str, body: PredictRequest, version: str = "latest"):
    ab_routed = False

    if version == "latest":
        ab_versions = ModelRegistry.get_ab_versions(model_name)
        if len(ab_versions) >= 2:
            version = get_ab_version(ab_versions)
            ab_routed = True

    model = ModelRegistry.get(model_name, version)
    if model is None:
        raise HTTPException(404, f"Model '{model_name}' version '{version}' not loaded")

    start = time.perf_counter()
    predictions = model.predict(body.features)
    probabilities = None
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(body.features).tolist()
    latency_ms = (time.perf_counter() - start) * 1000

    ground_truth = [body.label] if body.label is not None else None
    await log_prediction(
        model_name=model_name,
        version=version,
        features=body.features,
        predictions=predictions.tolist(),
        latency_ms=latency_ms,
        ground_truth=ground_truth,
    )

    return PredictResponse(
        model_name=model_name,
        model_version=version,
        ab_routed=ab_routed,
        predictions=predictions.tolist(),
        probabilities=probabilities,
        latency_ms=round(latency_ms, 2),
    )

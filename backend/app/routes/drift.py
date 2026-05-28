from fastapi import APIRouter, Query
from datetime import date

from app.utils.drift import compute_drift_report
from app.schemas.drift import DriftReport

router = APIRouter(prefix="/drift", tags=["drift"])


@router.get("/{model_name}", response_model=DriftReport)
async def get_drift(
    model_name: str,
    since: date = Query(default=None),
    version: str = "latest",
):
    report = await compute_drift_report(model_name, version, since)
    return report

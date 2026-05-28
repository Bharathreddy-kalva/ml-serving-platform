from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.middleware.logging import RequestLoggingMiddleware
from app.routes import health, inference, models, drift, ab_test, retrain
from app.utils.db import close_db, init_db
from app.utils.model_loader import ModelRegistry
from app.utils.retrainer import drift_check_job

_scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(settings.database_url)
    await ModelRegistry.load_production_models()

    _scheduler.add_job(
        drift_check_job,
        trigger="interval",
        seconds=settings.retrain_check_interval,
        id="drift_check",
        max_instances=1,       # never overlap; skip if previous tick is still running
        coalesce=True,
    )
    _scheduler.start()

    yield

    _scheduler.shutdown(wait=False)
    ModelRegistry.clear()
    await close_db()


app = FastAPI(
    title="ML Serving Platform",
    version="1.0.0",
    description="Inference API with versioned scikit-learn models, A/B testing, and auto-retraining",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(health.router)
app.include_router(inference.router, prefix="/api")
app.include_router(models.router,    prefix="/api")
app.include_router(drift.router,     prefix="/api")
app.include_router(ab_test.router,   prefix="/api")
app.include_router(retrain.router,   prefix="/api")

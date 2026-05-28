from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.middleware.logging import RequestLoggingMiddleware
from app.routes import health, inference, models, drift, ab_test
from app.utils.model_loader import ModelRegistry


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ModelRegistry.load_production_models()
    yield
    ModelRegistry.clear()


app = FastAPI(
    title="ML Serving Platform",
    version="1.0.0",
    description="Inference API with versioned scikit-learn models and A/B testing",
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
app.include_router(models.router, prefix="/api")
app.include_router(drift.router, prefix="/api")
app.include_router(ab_test.router, prefix="/api")

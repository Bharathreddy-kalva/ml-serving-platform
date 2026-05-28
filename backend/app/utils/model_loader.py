import logging
from datetime import datetime

import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient

from app.config import settings
from app.schemas.models import ModelInfo

logger = logging.getLogger(__name__)

# Stages that qualify a version for A/B serving. "None" is the local-dev fallback.
_AB_STAGES = {"Production", "Staging"}
_FALLBACK_STAGES = {"None"}


class ModelRegistry:
    _models: dict[str, object] = {}
    _info: dict[str, ModelInfo] = {}

    @classmethod
    def _key(cls, name: str, version: str) -> str:
        return f"{name}:{version}"

    @classmethod
    async def load_production_models(cls):
        mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        client = MlflowClient()

        registered = client.search_registered_models()
        if not registered:
            logger.warning("No registered models found at %s", settings.mlflow_tracking_uri)
            return

        for rm in registered:
            all_versions = sorted(
                client.search_model_versions(f"name='{rm.name}'"),
                key=lambda v: int(v.version),
            )

            # Prefer Production + Staging for A/B; fall back to "None" stage for local dev
            to_load = [v for v in all_versions if v.current_stage in _AB_STAGES]
            if not to_load:
                to_load = [v for v in all_versions if v.current_stage in _FALLBACK_STAGES]
                if to_load:
                    to_load = [to_load[-1]]   # highest "None"-stage version only

            if not to_load:
                logger.warning("No loadable version found for model '%s'", rm.name)
                continue

            # "latest" points to the Production version, or the highest available
            production = [v for v in to_load if v.current_stage == "Production"]
            latest_mv = production[-1] if production else to_load[-1]

            for mv in to_load:
                model_uri = f"models:/{rm.name}/{mv.version}"
                try:
                    pipeline = mlflow.sklearn.load_model(model_uri)
                except Exception as exc:
                    logger.error("Failed to load '%s' v%s: %s", rm.name, mv.version, exc)
                    continue

                run = client.get_run(mv.run_id)
                info = ModelInfo(
                    name=rm.name,
                    version=str(mv.version),
                    stage=mv.current_stage,
                    registered_at=datetime.fromtimestamp(mv.creation_timestamp / 1000),
                    run_id=mv.run_id,
                    metrics=dict(run.data.metrics),
                )
                cls._models[cls._key(rm.name, mv.version)] = pipeline
                cls._info[cls._key(rm.name, mv.version)] = info
                logger.info("Loaded '%s' v%s (stage=%s)", rm.name, mv.version, mv.current_stage)

            # Register "latest" alias
            latest_key = cls._key(rm.name, str(latest_mv.version))
            if latest_key in cls._models:
                cls._models[cls._key(rm.name, "latest")] = cls._models[latest_key]
                cls._info[cls._key(rm.name, "latest")] = cls._info[latest_key]

    @classmethod
    def get(cls, name: str, version: str = "latest"):
        return cls._models.get(cls._key(name, version))

    @classmethod
    def get_info(cls, name: str, version: str = "latest") -> ModelInfo | None:
        return cls._info.get(cls._key(name, version))

    @classmethod
    def get_ab_versions(cls, model_name: str) -> list[str]:
        """Return all loaded numeric version strings for a model, sorted ascending."""
        return sorted(
            [
                key.split(":", 1)[1]
                for key in cls._models
                if key.startswith(f"{model_name}:") and not key.endswith(":latest")
            ],
            key=lambda v: int(v) if v.isdigit() else 0,
        )

    @classmethod
    def list_loaded(cls) -> list[ModelInfo]:
        """Return every loaded version (not the 'latest' alias)."""
        return [info for key, info in cls._info.items() if not key.endswith(":latest")]

    @classmethod
    def clear(cls):
        cls._models.clear()
        cls._info.clear()

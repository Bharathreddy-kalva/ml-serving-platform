from pathlib import Path
from pydantic_settings import BaseSettings

# Absolute path so it works regardless of working directory when the app starts
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_MLFLOW_URI = f"sqlite:///{_REPO_ROOT}/ml/artifacts/mlflow_backend/mlflow.db"


class Settings(BaseSettings):
    database_url: str = "postgresql://mlserving:changeme@localhost:5432/mlserving"

    # SQLite path works for local dev; override with http://mlflow:5000 in Docker/prod
    mlflow_tracking_uri: str = _DEFAULT_MLFLOW_URI
    # Stages tried in order; first match wins. Keeps local ("None") and prod ("Production") working.
    mlflow_model_stages: list[str] = ["Production", "Staging", "None"]
    s3_model_bucket: str = "mlserving-models"

    # Percentage of /predict traffic routed to the lower (Staging) version.
    # 50 means 50 % → v1 (Staging), 50 % → v2 (Production).
    ab_split_percent: int = 50

    api_secret_key: str = "changeme-secret"
    backend_cors_origins: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"


settings = Settings()

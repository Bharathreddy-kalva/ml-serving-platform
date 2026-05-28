# ML Model Serving & Monitoring Platform — CLAUDE.md

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | Python 3.11, FastAPI, Uvicorn |
| ML Models | scikit-learn (joblib serialization), MLflow |
| Frontend | React 18, TypeScript, Recharts |
| Database | PostgreSQL 15, Alembic migrations |
| Containerisation | Docker, Docker Compose |
| Cloud | AWS ECS Fargate, RDS, ECR, S3 |
| Observability | MLflow Tracking Server, Prometheus, Grafana |

## Models

All models are **scikit-learn** based and serialized with `joblib`.
Model artefacts are stored in `s3://mlserving-models/<model_name>/<version>/model.joblib`.
MLflow is the single source of truth for experiment runs and registered model versions.

## Folder Map

| Folder | Purpose |
|---|---|
| `/backend` | FastAPI inference API — loads versioned models, exposes `/predict`, `/health`, `/models` endpoints |
| `/frontend` | React dashboard — shows prediction logs, feature drift charts, model performance over time |
| `/ml` | Training scripts, feature engineering, MLflow experiment tracking, model registration |
| `/infra` | Docker Compose for local dev; Terraform / CloudFormation for AWS ECS + RDS + ECR |
| `/database` | PostgreSQL schema and Alembic migration files — predictions log, drift metrics, model registry metadata |

## Environment Variables

- All secrets and config live in `.env` files.
- **Never commit `.env` files** — they are git-ignored.
- Use `.env.example` as the template (committed, no real values).
- Each sub-project has its own `.env.example` (`backend/.env.example`, etc.).
- In production, variables are injected via AWS Secrets Manager / ECS task definitions.

## Key Conventions

- Backend: one route file per resource (`routes/inference.py`, `routes/models.py`, `routes/health.py`).
- Versioning: models are addressed as `<name>/<version>` — version is a semver string or `latest`.
- Migrations: always create a new Alembic revision; never edit existing ones.
- Frontend API calls go through `src/api/client.ts`; raw `fetch` calls elsewhere are a bug.
- Tests live next to source (`backend/tests/`, `ml/tests/`); run with `pytest`.

## Local Dev Quick-Start

```bash
cp .env.example .env          # fill in values
docker compose up --build     # starts postgres, mlflow, backend, frontend
```

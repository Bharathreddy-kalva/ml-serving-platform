# ML Model Serving & Monitoring Platform

A production-grade monorepo for training, serving, and monitoring scikit-learn models at scale.

---

## Architecture Overview

```
                        ┌─────────────────────────────────────────────────────┐
                        │                      AWS Cloud                       │
                        │                                                       │
  Browser ─────────────▶│  CloudFront ──▶ S3 (React SPA)                       │
                        │                                                       │
  API Client ──────────▶│  ALB ──▶ ECS Fargate (FastAPI)  ──▶ RDS PostgreSQL   │
                        │               │                                       │
                        │               ▼                                       │
                        │          S3 Model Artefacts                           │
                        │               │                                       │
                        │               ▼                                       │
                        │       MLflow Tracking Server                          │
                        └─────────────────────────────────────────────────────┘

  Local Dev:  docker compose up  ──▶  all services on localhost
```

### Data Flow

1. **Training** — `ml/scripts/train.py` fits a scikit-learn pipeline, logs metrics + artefacts to MLflow, then registers the model version.
2. **Promotion** — a CI job (or manual step) transitions the MLflow model stage to `Production`.
3. **Serving** — the FastAPI backend loads the `Production` model from the MLflow registry on startup (or hot-reload on `/models/reload`). Each prediction is written to the `predictions` table in PostgreSQL.
4. **Monitoring** — the React dashboard polls `/api/drift` and `/api/metrics` to render feature-drift charts and performance KPIs. Alarms fire when PSI > 0.2 or accuracy drops > 5 pp.

---

## Repository Layout

```
ml-serving-platform/
├── backend/                 # FastAPI inference API
│   ├── app/
│   │   ├── main.py          # App factory, lifespan, CORS
│   │   ├── routes/          # inference.py, models.py, health.py, drift.py
│   │   ├── schemas/         # Pydantic request/response models
│   │   ├── middleware/      # Auth, logging, timing
│   │   └── utils/           # Model loader, drift calculator
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                # React monitoring dashboard
│   ├── src/
│   │   ├── api/             # Typed API client
│   │   ├── components/      # DriftChart, ModelCard, PredictionTable
│   │   ├── hooks/           # useMetrics, useDrift, useModels
│   │   └── pages/           # Dashboard, Models, Predictions
│   ├── Dockerfile
│   └── package.json
│
├── ml/                      # Training & evaluation
│   ├── scripts/             # train.py, evaluate.py, register.py
│   ├── configs/             # model YAML configs
│   └── notebooks/           # EDA and experiment notebooks
│
├── infra/                   # Infrastructure-as-code
│   ├── docker-compose.yml   # Local dev (all services)
│   ├── docker/              # Per-service Dockerfiles (referenced by compose)
│   ├── aws/
│   │   ├── ecs/             # Task definitions, service configs
│   │   ├── ecr/             # Image push scripts
│   │   └── rds/             # DB subnet group, parameter group
│   └── nginx/               # Reverse-proxy config for local dev
│
└── database/                # PostgreSQL
    ├── migrations/          # Alembic revision files
    └── seeds/               # Reference / test data
```

---

## Services (Local)

| Service | Port | Description |
|---|---|---|
| `backend` | 8000 | FastAPI inference API |
| `frontend` | 3000 | React dashboard (Vite dev server) |
| `postgres` | 5432 | PostgreSQL 15 |
| `mlflow` | 5001 | MLflow tracking server |
| `nginx` | 80 | Reverse proxy (routes `/api` → backend, `/` → frontend) |

---

## Quick Start

```bash
# 1. Clone and configure
git clone <repo>
cd ml-serving-platform
cp .env.example .env        # edit values

# 2. Start all services
docker compose -f infra/docker-compose.yml up --build

# 3. Run DB migrations
docker compose exec backend alembic upgrade head

# 4. Train and register a model
docker compose exec backend python ml/scripts/train.py

# 5. Open dashboard
open http://localhost:3000
```

---

## Tech Stack

- **Backend**: Python 3.11 · FastAPI · Uvicorn · SQLAlchemy · Alembic · joblib
- **ML**: scikit-learn · MLflow · pandas · numpy
- **Frontend**: React 18 · TypeScript · Vite · Recharts · TanStack Query
- **Database**: PostgreSQL 15
- **Infra**: Docker · Docker Compose · AWS ECS Fargate · RDS · ECR · S3

---

## Environment Variables

Copy `.env.example` to `.env` and fill in values. See `CLAUDE.md` for the full variable reference. Never commit real `.env` files.

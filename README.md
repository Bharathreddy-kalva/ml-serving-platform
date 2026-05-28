# ML Model Serving & Monitoring Platform

[![CI/CD](https://github.com/Bharathreddy-kalva/ml-serving-platform/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/Bharathreddy-kalva/ml-serving-platform/actions/workflows/ci-cd.yml)

A production-grade, fully Dockerised monorepo for training, serving, A/B testing, drift monitoring, and auto-retraining scikit-learn models.

---

## Quick Start

```bash
git clone <repo-url>
cd ml-serving-platform

make setup      # builds images, starts postgres+mlflow, trains both model versions
make up         # starts all five services

open http://localhost          # React dashboard
open http://localhost:8000/docs  # FastAPI Swagger
open http://localhost:5001       # MLflow UI
```

> **Prerequisites:** Docker ≥ 24 with Compose v2 (`docker compose`).

---

## Architecture

```
                           ┌──────────────────────────────────────────────┐
  Browser ────────────────▶│  nginx :80                                    │
                           │   /         → frontend:80  (React SPA)        │
                           │   /api/*    → backend:8000 (FastAPI)          │
                           └──────────────────────────┬───────────────────┘
                                                      │
                           ┌──────────────────────────▼───────────────────┐
                           │  FastAPI backend :8000                         │
                           │                                                │
                           │  ┌─────────────────────────────────────────┐  │
                           │  │  Inference routes                        │  │
                           │  │   POST /api/predict/{model}              │  │
                           │  │   A/B router  (Staging ↔ Production)     │  │
                           │  └───────────────┬─────────────────────────┘  │
                           │                  │ load models on startup      │
                           │  ┌───────────────▼─────────────────────────┐  │
                           │  │  MLflow client  ─────────────────────────┼──┼──▶  mlflow:5001
                           │  └─────────────────────────────────────────┘  │        │
                           │                                                │        ▼
                           │  ┌─────────────────────────────────────────┐  │  PostgreSQL :5432
                           │  │  APScheduler (60 s tick)                 │  │  (MLflow backend
                           │  │   drift check → PSI per feature          │  │   + predictions)
                           │  │   PSI > 0.2  → subprocess: train.py     │  │
                           │  └─────────────────────────────────────────┘  │
                           │                                                │
                           │  Prediction store → PostgreSQL (asyncpg)      │
                           │                     in-memory fallback (dev)  │
                           └────────────────────────────────────────────────┘
```

### Data flow

| Step | What happens |
|------|-------------|
| **Train** | `ml/scripts/train.py` fits a scikit-learn pipeline, logs params/metrics/model to MLflow, registers a new version |
| **Promote** | `ml/scripts/promote_ab.py` transitions v1 → Staging, v2 → Production |
| **Serve** | FastAPI loads all Production + Staging versions at startup via the MLflow registry |
| **A/B route** | Each `/predict` call is randomly split between Staging (v1) and Production (v2) at `AB_SPLIT_PERCENT` % |
| **Log** | Every prediction row (features, result, latency, label) is written to PostgreSQL |
| **Drift check** | Every 60 s the scheduler computes PSI per feature (first-half vs second-half of stored rows); PSI > 0.2 triggers auto-retrain |
| **Auto-retrain** | A subprocess runs `train.py` with `ml/configs/retrain.yaml`; the new version is registered in MLflow |
| **Monitor** | The React dashboard polls `/api/drift`, `/api/ab-stats`, and `/api/retrain-log` to render live charts |

---

## Services

| Service | Port | Description |
|---------|------|-------------|
| `nginx` | **80** | Reverse proxy — single public entry point |
| `backend` | 8000 | FastAPI: inference, A/B testing, drift, auto-retrain |
| `frontend` | — | React 18 + Tailwind dashboard (served through nginx) |
| `mlflow` | 5001 | MLflow tracking server + model registry (PostgreSQL backend) |
| `postgres` | 5432 | PostgreSQL 15 — predictions table + MLflow backend store |

---

## Features

### 1 — Versioned model inference

```
POST /api/predict/iris-classifier
{"features": [5.1, 3.5, 1.4, 0.2]}
```

Returns prediction, class probabilities, latency, and which version served it.
Flat `[f1, f2, f3, f4]` or batched `[[…], […]]` input both accepted.

### 2 — A/B testing

Two model versions are loaded simultaneously:
- **v1** (Staging) — RandomForest, 90% test accuracy
- **v2** (Production) — GradientBoosting, 93% test accuracy

Traffic split is configurable via `AB_SPLIT_PERCENT` (default 50 %).
`GET /api/ab-stats/{model}` returns per-version prediction count, latency, and accuracy.

### 3 — Feature drift detection

`GET /api/drift/{model}?version=1` computes PSI and KS-test for each feature by comparing the first half (reference) vs second half (current window) of stored predictions. A feature is flagged when PSI > 0.2.

### 4 — Auto-retraining

APScheduler checks drift every 60 seconds. When any feature drifts:
1. A subprocess runs `ml/scripts/train.py --config ml/configs/retrain.yaml`
2. A new MLflow model version is registered
3. The event (timestamp, trigger, new version, duration) is appended to `ml/artifacts/retrain_log.json`
4. A 10-minute cooldown prevents cascading retrain loops

Manual trigger: `POST /api/retrain/{model}` (also reachable from the "Trigger Retrain" button in the dashboard).

`GET /api/retrain-log` returns the last 10 events.

---

## Makefile reference

| Command | What it does |
|---------|-------------|
| `make setup` | Builds images; starts postgres + mlflow; trains v1 (RF) and v2 (GB); promotes stages |
| `make up` | Starts all five services with `--build` |
| `make down` | Stops everything and removes volumes |
| `make logs` | Tail logs from all services |
| `make retrain` | POST to `/api/retrain/iris-classifier` |
| `make simulate-drift` | Sends 50 shifted predictions to trigger drift detection |
| `make ps` | Show service health status |

---

## Repository layout

```
ml-serving-platform/
├── backend/              FastAPI inference API
│   ├── app/
│   │   ├── main.py       App factory, lifespan, CORS, APScheduler
│   │   ├── config.py     Settings (pydantic-settings, env vars)
│   │   ├── routes/       inference, models, drift, ab_test, retrain, health
│   │   ├── schemas/      Pydantic request/response models
│   │   └── utils/        model_loader, db, drift, ab_router, retrainer
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/             React 18 + TypeScript + Tailwind dashboard
│   ├── src/
│   │   ├── api/          Typed axios client
│   │   ├── components/   DriftChart, ModelCard, ABTestPanel, RetrainLogPanel
│   │   ├── hooks/        useModels, useDrift, useABStats, useRetrainLog
│   │   └── pages/        Dashboard (auto-selects v1, shows drift + A/B + retrain log)
│   ├── Dockerfile
│   └── nginx.conf        SPA server (try_files → index.html)
│
├── ml/                   Training & evaluation
│   ├── scripts/          train.py, promote_ab.py, simulate_drift.py, setup_ab.sh
│   └── configs/          default.yaml (RF), gradientboosting.yaml (GB), retrain.yaml
│
├── infra/
│   ├── docker-compose.yml
│   ├── docker/mlflow/Dockerfile   psycopg2-binary layer on top of official MLflow image
│   └── nginx/nginx.conf           Reverse proxy (port 80)
│
├── database/
│   └── migrations/       001_initial_schema.sql, 002_add_prediction_labels.sql
│
├── Makefile              setup / up / down / logs / retrain / simulate-drift
└── CLAUDE.md             Development conventions and tech-stack reference
```

---

## Environment variables

Copy `.env.example` to `.env` for local dev. In Docker all vars are set directly in `docker-compose.yml`.

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://mlserving:changeme@localhost:5432/mlserving` | asyncpg connection string |
| `MLFLOW_TRACKING_URI` | `sqlite:///…/mlflow.db` (local) / `http://mlflow:5001` (Docker) | MLflow server |
| `AB_SPLIT_PERCENT` | `50` | % of traffic routed to Staging (v1) |
| `RETRAIN_CHECK_INTERVAL` | `60` | Drift check interval in seconds |
| `RETRAIN_COOLDOWN_SECONDS` | `600` | Minimum seconds between auto-retrains per model |
| `RETRAIN_CONFIG` | `ml/configs/retrain.yaml` | Config file used for auto-retraining |
| `BACKEND_CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed CORS origins |

---

## Local development (no Docker)

```bash
# 1. Create venv and install ML deps
bash ml/setup.sh

# 2. Train models and set up A/B test
bash run_local.sh              # starts local MLflow, trains v1
bash ml/scripts/setup_ab.sh   # trains v2, promotes stages

# 3. Start the backend
bash backend/run_dev.sh        # FastAPI on :8000 (uses SQLite MLflow + in-memory store)

# 4. Start the frontend
bash frontend/run_dev.sh       # Vite on :3000

# 5. Seed drift data
.venv/bin/python ml/scripts/simulate_drift.py
```

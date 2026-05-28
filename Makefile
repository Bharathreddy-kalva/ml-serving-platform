COMPOSE = docker-compose -f infra/docker-compose.yml

.PHONY: setup up down logs retrain simulate-drift ps help

# ──────────────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  make setup           Build images, start postgres+mlflow, train initial models"
	@echo "  make up              Start all services (postgres, mlflow, backend, frontend, nginx)"
	@echo "  make down            Stop and remove all containers and volumes"
	@echo "  make logs            Tail logs from all services"
	@echo "  make retrain         Manually trigger model retraining via the API"
	@echo "  make simulate-drift  Send 50 shifted predictions to trigger drift detection"
	@echo "  make ps              Show running service status"
	@echo ""

# ──────────────────────────────────────────────────────────────────────────────
setup:
	@echo "==> Building backend image (includes ml/ training scripts)..."
	$(COMPOSE) build backend
	@echo ""
	@echo "==> Starting postgres and mlflow..."
	$(COMPOSE) up -d postgres mlflow
	@echo ""
	@echo "==> Waiting for MLflow to be ready (port 5001)..."
	@until curl -sf http://localhost:5001/health > /dev/null 2>&1; do printf '.'; sleep 3; done
	@echo " ready"
	@echo ""
	@echo "==> Training v1: RandomForest classifier..."
	$(COMPOSE) run --rm backend \
		sh -c "cd /repo && python ml/scripts/train.py \
		  --config ml/configs/default.yaml \
		  --model-name iris-classifier"
	@echo ""
	@echo "==> Training v2: GradientBoosting classifier..."
	$(COMPOSE) run --rm backend \
		sh -c "cd /repo && python ml/scripts/train.py \
		  --config ml/configs/gradientboosting.yaml \
		  --model-name iris-classifier"
	@echo ""
	@echo "==> Promoting: v1 → Staging, v2 → Production..."
	$(COMPOSE) run --rm backend \
		sh -c "cd /repo && python ml/scripts/promote_ab.py"
	@echo ""
	@echo "✓  Setup complete."
	@echo "   Run 'make up' to start the full platform, then open http://localhost"
	@echo ""

# ──────────────────────────────────────────────────────────────────────────────
up:
	@echo "==> Starting all services..."
	$(COMPOSE) up -d --build
	@echo ""
	@echo "==> Waiting for services to be healthy..."
	@sleep 8
	@$(COMPOSE) ps
	@echo ""
	@echo "  Dashboard  → http://localhost"
	@echo "  API docs   → http://localhost:8000/docs"
	@echo "  MLflow UI  → http://localhost:5001"
	@echo ""

# ──────────────────────────────────────────────────────────────────────────────
down:
	$(COMPOSE) down -v
	@echo "All services stopped and volumes removed."

# ──────────────────────────────────────────────────────────────────────────────
logs:
	$(COMPOSE) logs -f

# ──────────────────────────────────────────────────────────────────────────────
retrain:
	@echo "==> Triggering manual retraining for iris-classifier..."
	@curl -s -X POST http://localhost:8000/api/retrain/iris-classifier | python3 -m json.tool

# ──────────────────────────────────────────────────────────────────────────────
simulate-drift:
	@echo "==> Sending 50 shifted prediction requests to trigger drift detection..."
	@if [ -f .venv/bin/python ]; then \
		.venv/bin/python ml/scripts/simulate_drift.py; \
	else \
		$(COMPOSE) run --rm backend sh -c "cd /repo && python ml/scripts/simulate_drift.py"; \
	fi

# ──────────────────────────────────────────────────────────────────────────────
ps:
	$(COMPOSE) ps

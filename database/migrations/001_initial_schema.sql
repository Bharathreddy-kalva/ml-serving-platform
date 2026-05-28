-- Migration 001: prediction log table.
-- model_versions is intentionally absent — MLflow is the single source of truth
-- for model registry data and creates its own tables on startup.

BEGIN;

CREATE TABLE IF NOT EXISTS predictions (
    id              BIGSERIAL PRIMARY KEY,
    model_name      TEXT        NOT NULL,
    model_version   TEXT        NOT NULL,
    features        JSONB       NOT NULL,
    predictions     JSONB       NOT NULL,
    latency_ms      FLOAT,
    ground_truth    JSONB       DEFAULT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_predictions_model_created
    ON predictions (model_name, model_version, created_at DESC);

COMMIT;

-- Migration 001: initial schema
-- Creates core tables for prediction logging, model registry metadata, and drift snapshots.

BEGIN;

CREATE TABLE IF NOT EXISTS model_versions (
    id              SERIAL PRIMARY KEY,
    name            TEXT        NOT NULL,
    version         TEXT        NOT NULL,
    stage           TEXT        NOT NULL DEFAULT 'None',  -- None | Staging | Production | Archived
    mlflow_run_id   TEXT,
    registered_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (name, version)
);

CREATE INDEX idx_model_versions_name_stage ON model_versions (name, stage);

CREATE TABLE IF NOT EXISTS predictions (
    id              BIGSERIAL PRIMARY KEY,
    model_name      TEXT        NOT NULL,
    model_version   TEXT        NOT NULL,
    features        JSONB       NOT NULL,
    predictions     JSONB       NOT NULL,
    latency_ms      FLOAT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_predictions_model_created ON predictions (model_name, model_version, created_at DESC);

CREATE TABLE IF NOT EXISTS drift_snapshots (
    id                  SERIAL PRIMARY KEY,
    model_name          TEXT    NOT NULL,
    model_version       TEXT    NOT NULL,
    computed_at         DATE    NOT NULL DEFAULT CURRENT_DATE,
    total_predictions   INT     NOT NULL DEFAULT 0,
    drifted_features    INT     NOT NULL DEFAULT 0,
    feature_reports     JSONB   NOT NULL DEFAULT '[]',
    UNIQUE (model_name, model_version, computed_at)
);

COMMIT;

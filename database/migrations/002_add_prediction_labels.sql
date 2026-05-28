-- Migration 002: add ground-truth label column for post-hoc accuracy tracking.

BEGIN;

ALTER TABLE predictions
    ADD COLUMN IF NOT EXISTS ground_truth JSONB DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS labelled_at  TIMESTAMPTZ DEFAULT NULL;

COMMIT;

-- Seed: insert a sample model version for local development

INSERT INTO model_versions (name, version, stage, mlflow_run_id)
VALUES ('iris-classifier', '1', 'Production', 'local-run-001')
ON CONFLICT (name, version) DO NOTHING;

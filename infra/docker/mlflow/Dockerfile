FROM ghcr.io/mlflow/mlflow:v2.13.0
# psycopg2-binary: PostgreSQL backend store support
# curl: used by the health check
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir psycopg2-binary

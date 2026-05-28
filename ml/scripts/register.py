"""Transition the latest model version to a target stage."""

import argparse

import mlflow
from mlflow.tracking import MlflowClient


def main(model_name: str, version: str, stage: str, tracking_uri: str):
    mlflow.set_tracking_uri(tracking_uri)
    client = MlflowClient()

    if version == "latest":
        versions = client.get_latest_versions(model_name, stages=["None", "Staging"])
        if not versions:
            raise SystemExit(f"No candidate versions found for '{model_name}'")
        version = versions[-1].version

    client.transition_model_version_stage(
        name=model_name,
        version=version,
        stage=stage,
        archive_existing_versions=(stage == "Production"),
    )
    print(f"Transitioned {model_name} v{version} → {stage}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-name", default="iris-classifier")
    parser.add_argument("--version", default="latest")
    parser.add_argument("--stage", default="Production")
    parser.add_argument("--tracking-uri", default="http://localhost:5001")
    args = parser.parse_args()
    main(args.model_name, args.version, args.stage, args.tracking_uri)

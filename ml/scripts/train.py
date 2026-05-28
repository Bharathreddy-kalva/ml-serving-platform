"""Train a scikit-learn pipeline and log it to MLflow."""

import argparse
import json
import os
from pathlib import Path

import mlflow
import mlflow.sklearn
import numpy as np
import yaml
from sklearn.datasets import load_iris
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def build_pipeline(cfg: dict) -> Pipeline:
    clf_type = cfg.get("classifier_type", "random_forest")

    if clf_type == "gradient_boosting":
        clf = GradientBoostingClassifier(
            n_estimators=cfg.get("n_estimators", 200),
            learning_rate=cfg.get("learning_rate", 0.05),
            max_depth=cfg.get("max_depth", 3),
            subsample=cfg.get("subsample", 0.8),
            random_state=cfg.get("random_state", 42),
        )
    else:
        clf = RandomForestClassifier(
            n_estimators=cfg.get("n_estimators", 100),
            max_depth=cfg.get("max_depth") or None,
            random_state=cfg.get("random_state", 42),
        )

    return Pipeline([("scaler", StandardScaler()), ("clf", clf)])


def _model_params(cfg: dict) -> dict:
    clf_type = cfg.get("classifier_type", "random_forest")
    base = {"classifier_type": clf_type, "random_state": cfg.get("random_state", 42)}
    if clf_type == "gradient_boosting":
        return {
            **base,
            "n_estimators": cfg.get("n_estimators", 200),
            "learning_rate": cfg.get("learning_rate", 0.05),
            "max_depth": cfg.get("max_depth", 3),
            "subsample": cfg.get("subsample", 0.8),
        }
    return {
        **base,
        "n_estimators": cfg.get("n_estimators", 100),
        "max_depth": cfg.get("max_depth") or "None",
    }


def save_feature_stats(X_train: np.ndarray, feature_names: list[str], out_path: Path) -> dict:
    stats = {
        name: {
            "mean": float(X_train[:, i].mean()),
            "std": float(X_train[:, i].std()),
            "min": float(X_train[:, i].min()),
            "max": float(X_train[:, i].max()),
            "p25": float(np.percentile(X_train[:, i], 25)),
            "p75": float(np.percentile(X_train[:, i], 75)),
        }
        for i, name in enumerate(feature_names)
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(stats, indent=2))
    return stats


def main(config_path: str, model_name: str):
    cfg = load_config(config_path)

    # Env var takes precedence so the retrainer subprocess inherits the backend's URI
    mlflow_uri = os.environ.get("MLFLOW_TRACKING_URI") or cfg.get("mlflow_tracking_uri", "http://localhost:5000")
    mlflow.set_tracking_uri(mlflow_uri)
    mlflow.set_experiment(cfg.get("experiment_name", "iris-classifier-v1"))

    dataset = load_iris()
    X, y = dataset.data, dataset.target
    feature_names: list[str] = list(dataset.feature_names)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = build_pipeline(cfg)

    with mlflow.start_run() as run:
        mlflow.log_params(_model_params(cfg))

        pipeline.fit(X_train, y_train)

        cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring="accuracy")
        test_accuracy = float(pipeline.score(X_test, y_test))

        mlflow.log_metrics(
            {
                "cv_accuracy_mean": float(cv_scores.mean()),
                "cv_accuracy_std": float(cv_scores.std()),
                "test_accuracy": test_accuracy,
                "train_samples": len(X_train),
                "test_samples": len(X_test),
            }
        )

        stats_path = Path("ml/artifacts/feature_stats.json")
        save_feature_stats(X_train, feature_names, stats_path)
        mlflow.log_artifact(str(stats_path), artifact_path="drift_baseline")

        model_info = mlflow.sklearn.log_model(
            pipeline,
            artifact_path="model",
            registered_model_name=model_name,
            input_example=X_train[:3],
        )

        print(f"\n{'='*55}")
        print(f"  Classifier  : {cfg.get('classifier_type', 'random_forest')}")
        print(f"  Run ID      : {run.info.run_id}")
        print(f"  Model URI   : {model_info.model_uri}")
        print(f"  Test acc    : {test_accuracy:.4f}")
        print(f"  CV acc      : {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
        print(f"{'='*55}\n")

        return run.info.run_id


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train iris-classifier pipeline")
    parser.add_argument("--config", default="ml/configs/default.yaml")
    parser.add_argument("--model-name", default="iris-classifier")
    args = parser.parse_args()
    main(args.config, args.model_name)

"""Evaluate a registered MLflow model against a held-out dataset."""

import argparse
import json

import mlflow
import mlflow.sklearn
import numpy as np
from sklearn.datasets import load_iris
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split


def main(model_name: str, stage: str, tracking_uri: str):
    mlflow.set_tracking_uri(tracking_uri)
    model_uri = f"models:/{model_name}/{stage}"
    pipeline = mlflow.sklearn.load_model(model_uri)

    X, y = load_iris(return_X_y=True)
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    preds = pipeline.predict(X_test)
    report = classification_report(y_test, preds, output_dict=True)
    cm = confusion_matrix(y_test, preds).tolist()

    print(json.dumps({"report": report, "confusion_matrix": cm}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-name", default="iris-classifier")
    parser.add_argument("--stage", default="Production")
    parser.add_argument("--tracking-uri", default="http://localhost:5001")
    args = parser.parse_args()
    main(args.model_name, args.stage, args.tracking_uri)

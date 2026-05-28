#!/usr/bin/env python3
"""Simulate feature drift for iris-classifier.

Phase 1 (requests 1-25):  25 real Iris samples spanning all 3 classes → no drift.
Phase 2 (requests 26-50): same samples with +2.0 added to every feature → clear drift.

Requests go to ?version=1 to bypass A/B routing so the 50 rows arrive in strict
order at the backend.  The drift computation splits them in half:
  reference = rows 1-25  (normal distribution)
  current   = rows 26-50 (shifted distribution)
This produces a clean PSI signal on every feature.

Usage (from repo root):
    .venv/bin/python ml/scripts/simulate_drift.py
"""

import json
import sys
import time
import urllib.request
import urllib.error

# ── Iris samples --one per "slot", stratified across all three classes ────────
# Drawn from the real sklearn Iris dataset.
# 8 setosa + 8 versicolor + 9 virginica = 25 samples.
NORMAL_SAMPLES: list[tuple[list[float], int]] = [
    # [sepal_len, sepal_wid, petal_len, petal_wid], class
    ([5.1, 3.5, 1.4, 0.2], 0), ([4.9, 3.0, 1.4, 0.2], 0), ([4.7, 3.2, 1.3, 0.2], 0),
    ([4.6, 3.1, 1.5, 0.2], 0), ([5.0, 3.6, 1.4, 0.2], 0), ([5.4, 3.9, 1.7, 0.4], 0),
    ([4.6, 3.4, 1.4, 0.3], 0), ([5.0, 3.4, 1.5, 0.2], 0),
    ([7.0, 3.2, 4.7, 1.4], 1), ([6.4, 3.2, 4.5, 1.5], 1), ([6.9, 3.1, 4.9, 1.5], 1),
    ([5.5, 2.3, 4.0, 1.3], 1), ([6.5, 2.8, 4.6, 1.5], 1), ([5.7, 2.8, 4.5, 1.3], 1),
    ([6.3, 3.3, 4.7, 1.6], 1), ([4.9, 2.4, 3.3, 1.0], 1),
    ([6.3, 3.3, 6.0, 2.5], 2), ([5.8, 2.7, 5.1, 1.9], 2), ([7.1, 3.0, 5.9, 2.1], 2),
    ([6.3, 2.9, 5.6, 1.8], 2), ([6.5, 3.0, 5.8, 2.2], 2), ([7.6, 3.0, 6.6, 2.1], 2),
    ([4.9, 2.5, 4.5, 1.7], 2), ([7.3, 2.9, 6.3, 1.8], 2), ([6.7, 2.5, 5.8, 1.8], 2),
]
assert len(NORMAL_SAMPLES) == 25, "Expected exactly 25 normal samples"

SHIFT = 2.0  # magnitude of distribution shift for phase 2

BACKEND = "http://localhost:8000"


def predict(features: list[float], label: int, version: str = "1") -> dict:
    url = f"{BACKEND}/api/predict/iris-classifier?version={version}"
    payload = json.dumps({"features": features, "label": label}).encode()
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def run():
    print(f"\nSimulating drift for iris-classifier (version 1)")
    print("=" * 56)

    # Phase 1 — normal distribution
    print(f"\nPhase 1: 25 normal Iris samples (no drift expected)")
    v1_correct = 0
    for i, (features, label) in enumerate(NORMAL_SAMPLES, 1):
        try:
            result = predict(features, label)
            pred = result["predictions"][0]
            correct = pred == label
            v1_correct += int(correct)
            mark = "✓" if correct else "✗"
            print(f"  [{i:02d}] {mark}  pred={pred}  served_by=v{result['model_version']}  {result['latency_ms']:.1f}ms")
        except urllib.error.URLError as e:
            print(f"  [{i:02d}] ERROR: {e.reason}  (is the backend running on port 8000?)", file=sys.stderr)
            sys.exit(1)
        time.sleep(0.05)  # small delay to avoid hammering

    # Phase 2 — shifted distribution (+2.0 on all features)
    print(f"\nPhase 2: 25 shifted samples (+{SHIFT} on all features → drift expected)")
    v2_correct = 0
    for i, (features, label) in enumerate(NORMAL_SAMPLES, 26):
        shifted = [round(f + SHIFT, 1) for f in features]
        try:
            result = predict(shifted, label)
            pred = result["predictions"][0]
            correct = pred == label
            v2_correct += int(correct)
            mark = "✓" if correct else "✗"
            print(f"  [{i:02d}] {mark}  pred={pred}  served_by=v{result['model_version']}  {result['latency_ms']:.1f}ms")
        except urllib.error.URLError as e:
            print(f"  [{i:02d}] ERROR: {e.reason}", file=sys.stderr)
            sys.exit(1)
        time.sleep(0.05)

    # Summary
    print("\n" + "=" * 56)
    print(f"  Requests sent    : 50 (all to version 1)")
    print(f"  Normal accuracy  : {v1_correct}/25  ({v1_correct/25*100:.0f}%)")
    print(f"  Shifted accuracy : {v2_correct}/25  ({v2_correct/25*100:.0f}%)  ← lower = drift confirmed")

    # Fetch drift report
    print("\nDrift report:")
    try:
        url = f"{BACKEND}/api/drift/iris-classifier?version=1"
        with urllib.request.urlopen(url, timeout=10) as resp:
            report = json.loads(resp.read())
        print(f"  Total predictions : {report['total_predictions']}")
        print(f"  Drifted features  : {report['drifted_features']}")
        print()
        for f in report["features"]:
            flag = "🔴 DRIFTED" if f["drifted"] else "🟢 stable "
            print(f"  {flag}  {f['feature_name']:20s}  PSI={f['psi']:.4f}")
    except Exception as e:
        print(f"  Could not fetch drift report: {e}", file=sys.stderr)

    print("\nDone. Open http://localhost:3000 and click the v1 model card to see the chart.\n")


if __name__ == "__main__":
    run()

"""Train a surrogate regressor to predict the IsolationForest decision score
and export it to ONNX for portable inference with onnxruntime.

This script uses the existing `TelemetrySimulator` to generate training data
and `AnomalyEngine` to label points with isolation scores. It then fits a
RandomForestRegressor and exports it to `models/surrogate_score.onnx`.
"""
from __future__ import annotations

import os
from pathlib import Path
import sys
import numpy as np

# Ensure repository root is on sys.path so `app` package imports work when
# this script is executed directly.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sklearn.ensemble import RandomForestRegressor
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType

from app.simulator.generator import TelemetrySimulator
from app.ai.engines.isolation_forest import AnomalyEngine, FEATURE_NAMES


def collect_training_data(n_history=200, n_samples=1000, seed: int | None = 42):
    sim = TelemetrySimulator(seed=seed)
    engine = AnomalyEngine(contamination=0.05, min_training_samples=30)

    # Build a running history of normal points
    history = [sim.generate_point(satellite_id="SAT-ONNX") for _ in range(n_history)]

    X = []
    y = []
    for _ in range(n_samples):
        pt = sim.generate_point(satellite_id="SAT-ONNX")
        # compute score using the AnomalyEngine with current history
        result = engine.evaluate(pt, history)
        # If the engine did not have enough training samples, append to history and continue
        if result.score is None:
            history.append(pt)
            if len(history) > n_history:
                history.pop(0)
            continue
        features = [float(getattr(pt, f)) for f in FEATURE_NAMES]
        X.append(features)
        y.append(result.score)
        history.append(pt)
        if len(history) > n_history:
            history.pop(0)

    return np.array(X, dtype=float), np.array(y, dtype=float)


def train_and_export(output_path: str = "models/surrogate_score.onnx") -> None:
    X, y = collect_training_data()
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)

    # export to ONNX
    initial_type = [("input", FloatTensorType([None, X.shape[1]]))]
    onx = convert_sklearn(model, initial_types=initial_type)

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(onx.SerializeToString())

    print("Exported surrogate model to", out_path)


if __name__ == "__main__":
    train_and_export()

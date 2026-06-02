from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict

import numpy as np
from sklearn.ensemble import RandomForestRegressor

FEATURE_NAMES = (
    "battery_voltage",
    "solar_output",
    "cpu_temperature",
    "fuel_level",
    "signal_strength",
    "orientation_pitch",
    "orientation_yaw",
)


@dataclass
class ForecastResult:
    forecasts: List[Dict[str, float]]
    maintenance_risk: float


class PredictiveMaintenanceModel:
    """Simple windowed multi-output forecaster using RandomForest.

    Trains a regressor to predict the next timestep's full feature vector
    from a flattened window of previous timesteps. Also computes a
    heuristic maintenance risk score from forecasted values.
    """

    def __init__(self, window_size: int = 5, random_state: int = 42) -> None:
        self.window_size = window_size
        self.model: RandomForestRegressor | None = None
        self.random_state = random_state

    def _make_dataset(self, history: List[object]):
        matrix = np.array([[float(getattr(p, f)) for f in FEATURE_NAMES] for p in history], dtype=float)
        X = []
        y = []
        for i in range(len(matrix) - self.window_size):
            window = matrix[i : i + self.window_size].flatten()
            X.append(window)
            y.append(matrix[i + self.window_size])
        if not X:
            return None, None
        return np.vstack(X), np.vstack(y)

    def train(self, history: List[object]) -> None:
        X, y = self._make_dataset(history)
        if X is None:
            raise ValueError("not enough history to train")
        self.model = RandomForestRegressor(n_estimators=50, random_state=self.random_state)
        self.model.fit(X, y)

    def forecast(self, last_window: List[object], steps: int = 1) -> ForecastResult:
        if self.model is None:
            raise ValueError("model not trained")
        if len(last_window) < self.window_size:
            raise ValueError("insufficient last_window length")

        window = np.array([[float(getattr(p, f)) for f in FEATURE_NAMES] for p in last_window[-self.window_size:]])
        preds: List[Dict[str, float]] = []
        current = window.copy()
        for _ in range(steps):
            x = current.flatten().reshape(1, -1)
            ypred = self.model.predict(x)[0]
            pred_dict = {f: float(ypred[idx]) for idx, f in enumerate(FEATURE_NAMES)}
            preds.append(pred_dict)
            # slide window
            current = np.vstack([current[1:], ypred])

        risk = self._compute_risk(preds)
        return ForecastResult(forecasts=preds, maintenance_risk=risk)

    def _compute_risk(self, preds: List[Dict[str, float]]) -> float:
        # Heuristic: if battery or fuel drops below thresholds or temp rises -> increase risk
        risk = 0.0
        for p in preds:
            if p["battery_voltage"] < 24.0:
                risk = max(risk, 0.8)
            # if fuel falls below 30% consider elevated risk for maintenance
            if p["fuel_level"] < 30.0:
                risk = max(risk, 0.8)
            if p["fuel_level"] < 10.0:
                risk = max(risk, 0.95)
            if p["cpu_temperature"] > 85.0:
                risk = max(risk, 0.9)
            if p["signal_strength"] < -110.0:
                risk = max(risk, 0.6)
        return float(min(1.0, risk))

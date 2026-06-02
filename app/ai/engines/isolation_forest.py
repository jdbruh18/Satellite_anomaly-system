from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import IsolationForest

from app.schemas.telemetry import AnomalyResult

FEATURE_NAMES = (
    "battery_voltage",
    "solar_output",
    "cpu_temperature",
    "fuel_level",
    "signal_strength",
    "orientation_pitch",
    "orientation_yaw",
)

MIN_STD_BY_FEATURE = {
    "battery_voltage": 0.5,
    "solar_output": 5.0,
    "cpu_temperature": 3.0,
    "fuel_level": 1.0,
    "signal_strength": 3.0,
    "orientation_pitch": 1.0,
    "orientation_yaw": 1.0,
}


@dataclass(frozen=True)
class FeatureProfile:
    mean: float
    std: float

    def high_threshold(self, absolute_floor: float, sigma: float = 3.0) -> float:
        return max(self.mean + sigma * self.std, absolute_floor)

    def low_threshold(self, absolute_ceiling: float, sigma: float = 3.0) -> float:
        return max(self.mean - sigma * self.std, absolute_ceiling)


class AnomalyEngine:
    def __init__(
        self,
        contamination: float,
        min_training_samples: int,
    ) -> None:
        self.contamination = contamination
        self.min_training_samples = min_training_samples

    def evaluate(self, point: object, history: Sequence[object]) -> AnomalyResult:
        features = self._features(point)

        if len(history) < self.min_training_samples:
            return AnomalyResult(
                is_anomaly=False,
                score=None,
                reason="training_pending",
                severity="INFO",
                explanation="insufficient training data",
                recommended_action="Collect more telemetry to build training set",
                anomaly_types=[],
                features=features,
                training_sample_count=len(history),
            )

        profiles = self._profiles(history)
        model = IsolationForest(
            contamination=self.contamination,
            n_estimators=100,
            random_state=42,
        )
        model.fit(self._matrix(history))

        score = float(model.decision_function(self._matrix([point]))[0])
        isolation_anomaly = bool(model.predict(self._matrix([point]))[0] == -1)
        anomaly_types = self._classify(features, profiles, history)
        if isolation_anomaly and not anomaly_types:
            anomaly_types = ["multivariate_outlier"]
        is_anomaly = isolation_anomaly or bool(anomaly_types)

        severity = self._severity(is_anomaly, score, anomaly_types, features)
        explanation = self._explain(anomaly_types, features, score, isolation_anomaly)

        return AnomalyResult(
            is_anomaly=is_anomaly,
            score=score,
            reason=self._reason(isolation_anomaly, anomaly_types),
            severity=severity,
            explanation=explanation,
            recommended_action="",
            anomaly_types=anomaly_types,
            features=features,
            training_sample_count=len(history),
        )

    def _severity(self, is_anomaly: bool, score: float | None, anomaly_types: list[str], features: dict[str, float]) -> str:
        if not is_anomaly:
            return "INFO"
        # domain-critical types
        critical_types = {"fuel_anomaly", "temperature_spike"}
        if any(t in critical_types for t in anomaly_types):
            return "CRITICAL"
        if score is not None and score < -0.2:
            return "CRITICAL"
        return "WARNING"

    def _explain(self, anomaly_types: list[str], features: dict[str, float], score: float | None, isolation_anomaly: bool) -> str:
        parts: list[str] = []
        mapping = {
            "temperature_spike": lambda f: f"CPU temperature high ({f['cpu_temperature']}°C)",
            "power_drop": lambda f: f"Battery {f['battery_voltage']}V or solar output {f['solar_output']}W low",
            "signal_instability": lambda f: f"Signal strength low ({f['signal_strength']} dBm)",
            "fuel_anomaly": lambda f: f"Fuel level low ({f['fuel_level']}%) or sudden drop",
            "multivariate_outlier": lambda f: "Multivariate outlier detected",
        }

        for t in anomaly_types:
            if t in mapping:
                parts.append(mapping[t](features))
            else:
                parts.append(t)

        if isolation_anomaly and not anomaly_types:
            parts.append(f"model outlier (score={score:.3f})")

        if score is not None:
            parts.append(f"model_score={score:.3f}")

        return "; ".join(parts)

    def _matrix(self, points: Sequence[object]) -> np.ndarray:
        return np.array(
            [[float(getattr(point, feature)) for feature in FEATURE_NAMES] for point in points],
            dtype=float,
        )

    def _features(self, point: object) -> dict[str, float]:
        return {feature: float(getattr(point, feature)) for feature in FEATURE_NAMES}

    def _profiles(self, history: Sequence[object]) -> dict[str, FeatureProfile]:
        matrix = self._matrix(history)
        profiles: dict[str, FeatureProfile] = {}

        for index, feature in enumerate(FEATURE_NAMES):
            values = matrix[:, index]
            std = max(float(np.std(values)), MIN_STD_BY_FEATURE[feature])
            profiles[feature] = FeatureProfile(mean=float(np.mean(values)), std=std)

        return profiles

    def _classify(
        self,
        features: dict[str, float],
        profiles: dict[str, FeatureProfile],
        history: Sequence[object],
    ) -> list[str]:
        anomaly_types: list[str] = []

        if features["cpu_temperature"] >= profiles["cpu_temperature"].high_threshold(70.0):
            anomaly_types.append("temperature_spike")

        battery_drop = features["battery_voltage"] <= profiles[
            "battery_voltage"
        ].low_threshold(24.0)
        solar_drop = features["solar_output"] <= profiles["solar_output"].low_threshold(45.0)
        if battery_drop or solar_drop:
            anomaly_types.append("power_drop")

        if features["signal_strength"] <= profiles["signal_strength"].low_threshold(-90.0):
            anomaly_types.append("signal_instability")

        fuel_drop = features["fuel_level"] <= profiles["fuel_level"].low_threshold(10.0)
        sudden_fuel_drop = self._sudden_fuel_drop(features["fuel_level"], history)
        if fuel_drop or sudden_fuel_drop:
            anomaly_types.append("fuel_anomaly")

        return anomaly_types

    def _sudden_fuel_drop(self, fuel_level: float, history: Sequence[object]) -> bool:
        if not history:
            return False

        latest_fuel = float(getattr(history[0], "fuel_level"))
        return latest_fuel - fuel_level >= 5.0

    def _reason(self, isolation_anomaly: bool, anomaly_types: list[str]) -> str:
        if isolation_anomaly and anomaly_types and anomaly_types != ["multivariate_outlier"]:
            return "isolation_forest+domain_classifier"
        if isolation_anomaly:
            return "isolation_forest"
        if anomaly_types:
            return "domain_classifier"
        return "normal"

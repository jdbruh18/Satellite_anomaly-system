from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import random
import time
from typing import Any, Iterator


@dataclass(frozen=True)
class TelemetryRange:
    mean: float
    deviation: float
    minimum: float
    maximum: float

    def normal(self, rng: random.Random) -> float:
        value = rng.gauss(self.mean, self.deviation)
        return round(min(max(value, self.minimum), self.maximum), 3)


NORMAL_RANGES: dict[str, TelemetryRange] = {
    "battery_voltage": TelemetryRange(mean=27.5, deviation=0.6, minimum=25.5, maximum=29.2),
    "solar_output": TelemetryRange(mean=82.0, deviation=8.0, minimum=55.0, maximum=100.0),
    "cpu_temperature": TelemetryRange(mean=42.0, deviation=5.0, minimum=24.0, maximum=62.0),
    "fuel_level": TelemetryRange(mean=71.0, deviation=0.05, minimum=0.0, maximum=100.0),
    "signal_strength": TelemetryRange(mean=-68.0, deviation=4.0, minimum=-82.0, maximum=-52.0),
    "orientation_pitch": TelemetryRange(mean=0.0, deviation=1.2, minimum=-6.0, maximum=6.0),
    "orientation_yaw": TelemetryRange(mean=0.0, deviation=1.5, minimum=-8.0, maximum=8.0),
}

ANOMALY_RANGES: dict[str, tuple[tuple[float, float], ...]] = {
    "battery_voltage": ((18.0, 23.5),),
    "solar_output": ((0.0, 35.0),),
    "cpu_temperature": ((75.0, 105.0),),
    "fuel_level": ((0.0, 8.0),),
    "signal_strength": ((-118.0, -92.0),),
    "orientation_pitch": ((-35.0, -12.0), (12.0, 35.0)),
    "orientation_yaw": ((-55.0, -15.0), (15.0, 55.0)),
}


class SatelliteTelemetrySimulator:
    def __init__(
        self,
        satellite_id: str = "SAT-001",
        anomaly_rate: float = 0.06,
        seed: int | None = None,
    ) -> None:
        if not 0 <= anomaly_rate <= 1:
            raise ValueError("anomaly_rate must be between 0 and 1")

        self.satellite_id = satellite_id
        self.anomaly_rate = anomaly_rate
        self.rng = random.Random(seed)
        self.sequence = 0
        self._fuel_level = NORMAL_RANGES["fuel_level"].mean

    def generate(self) -> dict[str, Any]:
        self.sequence += 1
        telemetry = {
            name: value_range.normal(self.rng)
            for name, value_range in NORMAL_RANGES.items()
            if name != "fuel_level"
        }
        telemetry["fuel_level"] = self._next_fuel_level()

        anomaly_fields = self._inject_anomalies(telemetry)

        return {
            "satellite_id": self.satellite_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sequence": self.sequence,
            **telemetry,
            "is_anomaly": bool(anomaly_fields),
            "anomaly_fields": anomaly_fields,
        }

    def stream(self, interval_seconds: float = 1.0) -> Iterator[dict[str, Any]]:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be greater than 0")

        while True:
            yield self.generate()
            time.sleep(interval_seconds)

    def _next_fuel_level(self) -> float:
        burn = self.rng.uniform(0.002, 0.02)
        self._fuel_level = max(0.0, self._fuel_level - burn)
        return round(self._fuel_level, 3)

    def _inject_anomalies(self, telemetry: dict[str, float]) -> list[str]:
        if self.rng.random() >= self.anomaly_rate:
            return []

        field_count = 1 if self.rng.random() < 0.85 else 2
        anomaly_fields = self.rng.sample(list(ANOMALY_RANGES), k=field_count)

        for field in anomaly_fields:
            low, high = self.rng.choice(ANOMALY_RANGES[field])
            telemetry[field] = round(self.rng.uniform(low, high), 3)

        return anomaly_fields


def to_json_line(payload: dict[str, Any]) -> str:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)

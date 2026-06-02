from datetime import datetime, timezone
import random

from app.schemas.telemetry import TelemetryCreate


class TelemetrySimulator:
    def __init__(self, seed: int | None = None) -> None:
        self.random = random.Random(seed)

    def generate_point(
        self,
        satellite_id: str,
        anomaly_rate: float = 0.05,
    ) -> TelemetryCreate:
        is_injected_anomaly = self.random.random() < anomaly_rate

        if is_injected_anomaly:
            return self._anomalous_point(satellite_id)

        return TelemetryCreate(
            satellite_id=satellite_id,
            timestamp=datetime.now(timezone.utc),
            battery_voltage=self.random.gauss(27.5, 0.6),
            solar_output=max(0, min(100, self.random.gauss(82, 8))),
            cpu_temperature=self.random.gauss(42, 5),
            fuel_level=self.random.uniform(45, 95),
            signal_strength=self.random.gauss(-68, 4),
            orientation_pitch=self.random.gauss(0, 1.2),
            orientation_yaw=self.random.gauss(0, 1.5),
        )

    def _anomalous_point(self, satellite_id: str) -> TelemetryCreate:
        anomaly_type = self.random.choice(
            ["battery", "solar", "thermal", "fuel", "signal", "pitch", "yaw"]
        )

        base = self.generate_point(satellite_id=satellite_id, anomaly_rate=0)
        updates = {
            "battery": {"battery_voltage": self.random.uniform(18.0, 23.5)},
            "solar": {"solar_output": self.random.uniform(0.0, 35.0)},
            "thermal": {"cpu_temperature": self.random.uniform(75.0, 105.0)},
            "fuel": {"fuel_level": self.random.uniform(0.0, 8.0)},
            "signal": {"signal_strength": self.random.uniform(-118.0, -92.0)},
            "pitch": {"orientation_pitch": self.random.choice([-25.0, 25.0])},
            "yaw": {"orientation_yaw": self.random.choice([-40.0, 40.0])},
        }
        data = base.model_dump()
        data.update(updates[anomaly_type])
        return TelemetryCreate(**data)

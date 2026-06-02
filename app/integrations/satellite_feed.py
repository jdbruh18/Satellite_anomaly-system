from collections.abc import AsyncIterator
from typing import Protocol

from app.schemas.telemetry import TelemetryCreate
from app.simulator.generator import TelemetrySimulator


class TelemetryFeedClient(Protocol):
    async def read(self) -> AsyncIterator[TelemetryCreate]:
        """Yield telemetry points from an external satellite data source."""


class SimulatedTelemetryFeed:
    def __init__(
        self,
        satellite_id: str,
        anomaly_rate: float,
        seed: int | None = None,
    ) -> None:
        self.satellite_id = satellite_id
        self.anomaly_rate = anomaly_rate
        self.simulator = TelemetrySimulator(seed=seed)

    async def read(self) -> AsyncIterator[TelemetryCreate]:
        while True:
            yield self.simulator.generate_point(
                satellite_id=self.satellite_id,
                anomaly_rate=self.anomaly_rate,
            )


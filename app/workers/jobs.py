from app.services.telemetry_service import TelemetryService
from app.simulator.generator import TelemetrySimulator


async def ingest_simulated_batch(
    service: TelemetryService,
    satellite_id: str,
    count: int,
    anomaly_rate: float,
    seed: int | None = None,
) -> dict[str, int | str]:
    simulator = TelemetrySimulator(seed=seed)
    anomaly_count = 0

    for _ in range(count):
        point = simulator.generate_point(
            satellite_id=satellite_id,
            anomaly_rate=anomaly_rate,
        )
        ingested = await service.ingest(point)
        if ingested.anomaly_event.is_anomaly:
            anomaly_count += 1

    return {
        "satellite_id": satellite_id,
        "inserted": count,
        "anomalies_detected": anomaly_count,
    }

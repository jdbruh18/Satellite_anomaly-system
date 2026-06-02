"""Run the realtime telemetry processor against the configured telemetry feed."""
import argparse
import asyncio
import logging

from app.api.dependencies import get_telemetry_service
from app.integrations.satellite_feed import SimulatedTelemetryFeed
from app.pipeline.realtime import RealtimeProcessor
from app.core.config import get_settings
from app.db.session import AsyncSessionLocal


def main() -> None:
    parser = argparse.ArgumentParser(description="Run realtime telemetry processor")
    parser.add_argument("--satellite-id", default="SAT-001")
    parser.add_argument("--anomaly-rate", type=float, default=None)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    settings = get_settings()
    anomaly_rate = args.anomaly_rate if args.anomaly_rate is not None else settings.simulator_anomaly_rate

    logging.basicConfig(level=logging.INFO)

    async def _run() -> None:
        async with AsyncSessionLocal() as db:
            service = get_telemetry_service.__wrapped__(db=db, settings=settings)  # type: ignore[attr-defined]
            feed = SimulatedTelemetryFeed(satellite_id=args.satellite_id, anomaly_rate=anomaly_rate, seed=args.seed)
            processor = RealtimeProcessor(feed=feed, service=service)
            await processor.run()

    asyncio.run(_run())


if __name__ == "__main__":
    main()

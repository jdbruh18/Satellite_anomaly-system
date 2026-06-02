import argparse
import asyncio
import logging
from pathlib import Path
import sys

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.simulator.generator import TelemetrySimulator

logger = logging.getLogger(__name__)


async def run(args: argparse.Namespace) -> None:
    simulator = TelemetrySimulator(seed=args.seed)

    async with httpx.AsyncClient(base_url=args.api_url, timeout=10) as client:
        for index in range(args.count):
            point = simulator.generate_point(
                satellite_id=args.satellite_id,
                anomaly_rate=args.anomaly_rate,
            )
            response = await client.post(
                "/api/v1/telemetry",
                json=point.model_dump(mode="json"),
            )
            response.raise_for_status()
            payload = response.json()
            logger.info(
                "sent telemetry point",
                extra={
                    "index": index + 1,
                    "satellite_id": args.satellite_id,
                    "is_anomaly": payload["anomaly"]["is_anomaly"],
                    "score": payload["anomaly"]["score"],
                },
            )
            await asyncio.sleep(args.interval)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stream simulated telemetry to the API.")
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--satellite-id", default="SAT-001")
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--anomaly-rate", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=None)
    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(run(parse_args()))

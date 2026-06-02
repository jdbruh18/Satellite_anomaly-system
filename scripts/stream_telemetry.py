import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.simulator.telemetry_stream import SatelliteTelemetrySimulator, to_json_line


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stream simulated satellite telemetry as JSON lines."
    )
    parser.add_argument("--satellite-id", default="SAT-001")
    parser.add_argument("--anomaly-rate", type=float, default=0.06)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--count", type=int, default=0, help="0 streams forever.")
    parser.add_argument("--seed", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    simulator = SatelliteTelemetrySimulator(
        satellite_id=args.satellite_id,
        anomaly_rate=args.anomaly_rate,
        seed=args.seed,
    )

    for index, payload in enumerate(simulator.stream(args.interval), start=1):
        print(to_json_line(payload), flush=True)

        if args.count and index >= args.count:
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)

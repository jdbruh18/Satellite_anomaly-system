import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.alerts.manager import AlertManager
from app.integrations.satellite_feed import TelemetryFeedClient
from app.services.telemetry_service import TelemetryService
from app.db.repositories import AnomalyRepository

logger = logging.getLogger(__name__)


class AutonomousMonitor:
    def __init__(self, feed: TelemetryFeedClient, service: TelemetryService, report_dir: Optional[str] = None) -> None:
        self.feed = feed
        self.service = service
        self.alert_manager = AlertManager()
        self.report_dir = Path(report_dir or "reports")
        self.report_dir.mkdir(parents=True, exist_ok=True)

    async def run(self) -> None:
        logger.info("starting autonomous monitor loop")
        async for payload in self.feed.read():
            try:
                ingested = await self.service.ingest(payload)
                if ingested.anomaly_event and ingested.anomaly_event.is_anomaly:
                    # forward enriched alert
                    alert = {
                        "telemetry_id": ingested.telemetry.id,
                        "satellite_id": ingested.telemetry.satellite_id,
                        "severity": ingested.anomaly_event.severity,
                        "probable_cause": ingested.anomaly_event.explanation,
                        "recommended_action": ingested.anomaly_event.recommended_action,
                        "score": ingested.anomaly_event.score,
                        "anomaly_types": ingested.anomaly_event.anomaly_types,
                        "timestamp": ingested.anomaly_event.created_at.isoformat(),
                    }
                    await self.alert_manager.send_alert(alert)
                    # append to a daily incident report
                    await self._append_report(alert)
            except Exception:
                logger.exception("monitor loop error")

    async def _append_report(self, alert: dict) -> None:
        name = datetime.utcnow().strftime("incidents-%Y-%m-%d.jsonl")
        path = self.report_dir / name
        async with asyncio.to_thread(open, path, "a", encoding="utf8") as f:
            f.write(json.dumps(alert) + "\n")

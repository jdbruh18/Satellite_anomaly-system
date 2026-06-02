import asyncio
import logging
from typing import AsyncIterator

from app.alerts.manager import AlertManager
from app.integrations.satellite_feed import TelemetryFeedClient
from app.services.telemetry_service import TelemetryService
from app.db.session import init_db

logger = logging.getLogger(__name__)


class RealtimeProcessor:
    def __init__(self, feed: TelemetryFeedClient, service: TelemetryService) -> None:
        self.feed = feed
        self.service = service
        self.alert_manager = AlertManager()

    async def run(self) -> None:
        # Ensure DB schema exists before processing
        await init_db()
        logger.info("starting realtime telemetry processor")

        async for payload in self._iter_feed():
            try:
                result = await self.service.ingest(payload)
                if result.anomaly_event and result.anomaly_event.is_anomaly:
                    alert_payload = {
                        "telemetry_id": result.telemetry.id,
                        "satellite_id": result.telemetry.satellite_id,
                        "score": result.anomaly_event.score,
                        "anomaly_types": result.anomaly_event.anomaly_types,
                    }
                    await self.alert_manager.send_alert(alert_payload)
            except Exception:
                logger.exception("error processing telemetry point")

    async def _iter_feed(self) -> AsyncIterator:
        async for item in self.feed.read():
            yield item

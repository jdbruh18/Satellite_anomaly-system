import logging
import os
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class AlertManager:
    def __init__(self, webhook: str | None = None) -> None:
        settings = get_settings()
        self.webhook = webhook or settings.alert_webhook or os.getenv("ALERT_WEBHOOK")

    async def send_alert(self, payload: dict[str, Any]) -> None:
        """Send an alert. Currently posts to configured webhook or logs the alert."""
        if self.webhook:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    await client.post(self.webhook, json=payload)
                logger.info("alert forwarded to webhook", extra={"webhook": self.webhook})
            except Exception as exc:  # pragma: no cover - best-effort network call
                logger.exception("failed to forward alert", exc_info=exc)
        else:
            logger.warning("ALERT: anomaly detected", extra={"payload": payload})

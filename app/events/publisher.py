import logging
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class EventPublisher(Protocol):
    def publish(self, topic: str, payload: dict[str, Any]) -> None:
        """Publish a domain event to a queue, stream, or log sink."""


class LoggingEventPublisher:
    def publish(self, topic: str, payload: dict[str, Any]) -> None:
        logger.info("domain event published", extra={"topic": topic, "payload": payload})


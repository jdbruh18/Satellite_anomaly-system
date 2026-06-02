from dataclasses import dataclass
import logging

from app.ai.base import AnomalyDetector
from app.db.repositories import AnomalyRepository, TelemetryRepository
from app.events.publisher import EventPublisher
from app.models import AnomalyEvent, TelemetryPoint
from app.observability.metrics import metrics
from app.schemas.telemetry import TelemetryCreate
from app.ai.reasoning import explain_anomaly

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IngestedTelemetry:
    telemetry: TelemetryPoint
    anomaly_event: AnomalyEvent


class TelemetryService:
    def __init__(
        self,
        telemetry_repo: TelemetryRepository,
        anomaly_repo: AnomalyRepository,
        anomaly_engine: AnomalyDetector,
        history_window: int,
        event_publisher: EventPublisher | None = None,
    ) -> None:
        self.telemetry_repo = telemetry_repo
        self.anomaly_repo = anomaly_repo
        self.anomaly_engine = anomaly_engine
        self.history_window = history_window
        self.event_publisher = event_publisher

    async def ingest(self, payload: TelemetryCreate) -> IngestedTelemetry:
        logger.info(
            "telemetry received",
            extra={
                "satellite_id": payload.satellite_id,
                "sequence": payload.sequence,
            },
        )
        history = await self.telemetry_repo.list_recent_normal(
            limit=self.history_window,
            satellite_id=payload.satellite_id,
        )
        telemetry = await self.telemetry_repo.create(payload)
        anomaly_result = self.anomaly_engine.evaluate(payload, history)
        # Generate reasoning and suggested corrective actions
        reasoning = explain_anomaly(anomaly_result.features, anomaly_result.score, anomaly_result.anomaly_types)
        # attach recommended_action and possibly a richer explanation
        anomaly_result.recommended_action = reasoning.recommended_action
        # prefer reasoning.explanation to engine explanation if available
        if reasoning.explanation:
            anomaly_result.explanation = reasoning.explanation
        anomaly_event = await self.anomaly_repo.create(
            telemetry_id=telemetry.id,
            result=anomaly_result,
        )
        metrics.increment("telemetry_ingested_total")
        metrics.increment("anomaly_events_total")

        self._publish(
            "telemetry.ingested",
            {
                "telemetry_id": telemetry.id,
                "satellite_id": telemetry.satellite_id,
                "is_anomaly": anomaly_event.is_anomaly,
            },
        )

        if anomaly_event.is_anomaly:
            metrics.increment("anomalies_detected_total")
            logger.warning(
                "telemetry anomaly detected",
                extra={
                    "telemetry_id": telemetry.id,
                    "satellite_id": telemetry.satellite_id,
                    "score": anomaly_event.score,
                    "anomaly_types": anomaly_event.anomaly_types,
                    "severity": anomaly_event.severity,
                    "explanation": anomaly_event.explanation,
                },
            )
            self._publish(
                "telemetry.anomaly_detected",
                {
                    "telemetry_id": telemetry.id,
                    "satellite_id": telemetry.satellite_id,
                    "score": anomaly_event.score,
                    "anomaly_types": anomaly_event.anomaly_types,
                    "severity": anomaly_event.severity,
                    "explanation": anomaly_event.explanation,
                },
            )

        logger.info(
            "telemetry stored",
            extra={
                "telemetry_id": telemetry.id,
                "satellite_id": telemetry.satellite_id,
                "is_anomaly": anomaly_event.is_anomaly,
            },
        )
        return IngestedTelemetry(telemetry=telemetry, anomaly_event=anomaly_event)

    def _publish(self, topic: str, payload: dict[str, object]) -> None:
        if self.event_publisher is not None:
            self.event_publisher.publish(topic, payload)

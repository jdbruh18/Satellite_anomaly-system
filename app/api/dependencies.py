from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.engines import AnomalyEngine
from app.core.config import Settings, get_settings
from app.db.repositories import AnomalyRepository, TelemetryRepository
from app.db.session import get_db
from app.events.publisher import LoggingEventPublisher
from app.services.telemetry_service import TelemetryService


def get_telemetry_service(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TelemetryService:
    return TelemetryService(
        telemetry_repo=TelemetryRepository(db),
        anomaly_repo=AnomalyRepository(db),
        anomaly_engine=AnomalyEngine(
            contamination=settings.anomaly_contamination,
            min_training_samples=settings.anomaly_min_training_samples,
        ),
        event_publisher=LoggingEventPublisher(),
        history_window=settings.anomaly_window_size,
    )

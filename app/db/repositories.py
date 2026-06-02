from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AnomalyEvent, TelemetryPoint
from app.schemas.telemetry import AnomalyResult, TelemetryCreate


class TelemetryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, payload: TelemetryCreate) -> TelemetryPoint:
        point = TelemetryPoint(**payload.model_dump())
        self.db.add(point)
        await self.db.commit()
        await self.db.refresh(point)
        return point

    async def list_recent(
        self,
        limit: int,
        satellite_id: str | None = None,
    ) -> list[TelemetryPoint]:
        stmt = select(TelemetryPoint)
        if satellite_id:
            stmt = stmt.where(TelemetryPoint.satellite_id == satellite_id)

        stmt = stmt.order_by(desc(TelemetryPoint.timestamp)).limit(limit)
        result = await self.db.scalars(stmt)
        return list(result)

    async def list_recent_normal(
        self,
        limit: int,
        satellite_id: str | None = None,
    ) -> list[TelemetryPoint]:
        stmt = select(TelemetryPoint).join(AnomalyEvent).where(
            AnomalyEvent.is_anomaly.is_(False)
        )
        if satellite_id:
            stmt = stmt.where(TelemetryPoint.satellite_id == satellite_id)

        stmt = stmt.order_by(desc(TelemetryPoint.timestamp)).limit(limit)
        result = await self.db.scalars(stmt)
        return list(result)


class AnomalyRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self,
        telemetry_id: int,
        result: AnomalyResult,
    ) -> AnomalyEvent:
        event = AnomalyEvent(
            telemetry_id=telemetry_id,
            is_anomaly=result.is_anomaly,
            score=result.score,
            reason=result.reason,
            anomaly_types=result.anomaly_types,
            features=result.features,
            severity=getattr(result, "severity", "INFO"),
            explanation=getattr(result, "explanation", ""),
            recommended_action=getattr(result, "recommended_action", ""),
            training_sample_count=result.training_sample_count,
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def list_recent(
        self,
        limit: int,
        only_anomalies: bool = True,
    ) -> list[AnomalyEvent]:
        stmt = select(AnomalyEvent)
        if only_anomalies:
            stmt = stmt.where(AnomalyEvent.is_anomaly.is_(True))

        stmt = stmt.order_by(desc(AnomalyEvent.created_at)).limit(limit)
        result = await self.db.scalars(stmt)
        return list(result)

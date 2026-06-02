from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_telemetry_service
from app.db.repositories import TelemetryRepository
from app.db.session import get_db
from app.schemas.telemetry import (
    SimulationRequest,
    SimulationResponse,
    TelemetryCreate,
    TelemetryIngestResponse,
    TelemetryRead,
)
from app.services.telemetry_service import TelemetryService
from app.workers.jobs import ingest_simulated_batch

router = APIRouter()


@router.post(
    "",
    response_model=TelemetryIngestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_telemetry(
    payload: TelemetryCreate,
    service: TelemetryService = Depends(get_telemetry_service),
) -> TelemetryIngestResponse:
    ingested = await service.ingest(payload)
    return TelemetryIngestResponse(
        telemetry=ingested.telemetry,
        anomaly=ingested.anomaly_event,
    )


@router.get("", response_model=list[TelemetryRead])
async def list_telemetry(
    satellite_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> list[TelemetryRead]:
    return await TelemetryRepository(db).list_recent(limit=limit, satellite_id=satellite_id)


@router.post("/simulate", response_model=SimulationResponse)
async def simulate_telemetry(
    request: SimulationRequest,
    service: TelemetryService = Depends(get_telemetry_service),
) -> SimulationResponse:
    summary = await ingest_simulated_batch(
        service=service,
        satellite_id=request.satellite_id,
        count=request.count,
        anomaly_rate=request.anomaly_rate,
        seed=request.seed,
    )
    return SimulationResponse(**summary)

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import AnomalyRepository
from app.db.session import get_db
from app.schemas.telemetry import AnomalyEventRead

router = APIRouter()


@router.get("", response_model=list[AnomalyEventRead])
async def list_anomalies(
    only_anomalies: bool = Query(default=True),
    limit: int = Query(default=100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> list[AnomalyEventRead]:
    return await AnomalyRepository(db).list_recent(
        limit=limit,
        only_anomalies=only_anomalies,
    )

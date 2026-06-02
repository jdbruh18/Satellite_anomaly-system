from fastapi import APIRouter

from app.api.routes import anomalies, health, metrics, telemetry

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(telemetry.router, prefix="/telemetry", tags=["telemetry"])
api_router.include_router(anomalies.router, prefix="/anomalies", tags=["anomalies"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])

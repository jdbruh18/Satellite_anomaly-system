from fastapi import FastAPI

from app.schemas.telemetry import TelemetryCreate, AnomalyResult
from app.ai.engines import AnomalyEngine
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title="Anomaly Engine")

engine = AnomalyEngine(
    contamination=settings.anomaly_contamination,
    min_training_samples=settings.anomaly_min_training_samples,
)


@app.post("/score", response_model=AnomalyResult)
async def score(payload: TelemetryCreate):
    # For a standalone engine we have no history; return training_pending or model-only score
    return engine.evaluate(payload, history=[])

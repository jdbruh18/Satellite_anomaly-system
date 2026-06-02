from fastapi import APIRouter

from app.observability.metrics import metrics

router = APIRouter()


@router.get("")
def read_metrics() -> dict[str, int]:
    return metrics.snapshot()


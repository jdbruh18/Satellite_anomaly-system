from collections.abc import Sequence
from typing import Protocol

from app.schemas.telemetry import AnomalyResult


class AnomalyDetector(Protocol):
    def evaluate(self, point: object, history: Sequence[object]) -> AnomalyResult:
        """Score a telemetry point against historical telemetry."""


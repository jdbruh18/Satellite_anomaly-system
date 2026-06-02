from fastapi import FastAPI
import onnxruntime as ort
import numpy as np
from typing import Optional

from app.schemas.telemetry import TelemetryCreate, AnomalyResult
from app.ai.engines.isolation_forest import FEATURE_NAMES, AnomalyEngine, FeatureProfile
from app.simulator.generator import TelemetrySimulator

app = FastAPI(title="ONNX Anomaly Engine")


def _build_profiles_from_simulator(samples: int = 500, seed: Optional[int] = None):
    sim = TelemetrySimulator(seed=seed)
    points = [sim.generate_point(satellite_id="SAT-ONNX") for _ in range(samples)]
    engine = AnomalyEngine(contamination=0.05, min_training_samples=5)
    return engine._profiles(points)  # type: ignore[attr-defined]


MODEL_PATH = "models/surrogate_score.onnx"
if not ort.__name__:
    pass
session = ort.InferenceSession(MODEL_PATH)
input_name = session.get_inputs()[0].name

# precompute baseline profiles for domain classifier
PROFILES = _build_profiles_from_simulator()
ENGINE = AnomalyEngine(contamination=0.05, min_training_samples=5)


@app.post("/score", response_model=AnomalyResult)
async def score(payload: TelemetryCreate):
    features = np.array([[float(getattr(payload, f)) for f in FEATURE_NAMES]], dtype=np.float32)
    pred = session.run(None, {input_name: features})[0]
    # pred is the regression output predicting the isolation score
    score_val = float(pred[0])

    # simple threshold to decide anomaly from score
    isolation_anomaly = score_val < -0.2

    # domain classification using precomputed profiles
    feature_dict = {f: float(getattr(payload, f)) for f in FEATURE_NAMES}
    anomaly_types = ENGINE._classify(feature_dict, PROFILES, [])  # type: ignore[arg-type]

    is_anomaly = isolation_anomaly or bool(anomaly_types)

    reason = "onnx_surrogate"
    if isolation_anomaly and anomaly_types:
        reason = "onnx_surrogate+domain_classifier"
    elif isolation_anomaly:
        reason = "onnx_surrogate"
    elif anomaly_types:
        reason = "domain_classifier"

    return AnomalyResult(
        is_anomaly=is_anomaly,
        score=score_val,
        reason=reason,
        severity="CRITICAL" if is_anomaly and ("fuel_anomaly" in anomaly_types or "temperature_spike" in anomaly_types) else ("WARNING" if is_anomaly else "INFO"),
        explanation="; ".join([str(t) for t in anomaly_types]) or f"model_score={score_val:.3f}",
        recommended_action="",
        anomaly_types=anomaly_types,
        features=feature_dict,
        training_sample_count=0,
    )

from datetime import datetime, timezone

from app.schemas.telemetry import TelemetryCreate
from app.ai.engines import AnomalyEngine


def make_point(
    *,
    battery_voltage: float = 27.5,
    solar_output: float = 82.0,
    cpu_temperature: float = 42.0,
    fuel_level: float = 71.0,
    signal_strength: float = -68.0,
    orientation_pitch: float = 0.0,
    orientation_yaw: float = 0.0,
) -> TelemetryCreate:
    return TelemetryCreate(
        satellite_id="SAT-TEST",
        timestamp=datetime.now(timezone.utc),
        battery_voltage=battery_voltage,
        solar_output=solar_output,
        cpu_temperature=cpu_temperature,
        fuel_level=fuel_level,
        signal_strength=signal_strength,
        orientation_pitch=orientation_pitch,
        orientation_yaw=orientation_yaw,
    )


def test_engine_waits_for_training_window() -> None:
    engine = AnomalyEngine(contamination=0.05, min_training_samples=5)

    result = engine.evaluate(make_point(), history=[make_point()] * 4)

    assert result.is_anomaly is False
    assert result.reason == "training_pending"
    assert result.score is None
    assert result.anomaly_types == []


def test_engine_detects_temperature_spikes() -> None:
    engine = AnomalyEngine(contamination=0.05, min_training_samples=5)

    result = engine.evaluate(make_point(cpu_temperature=95), history=[make_point()] * 20)

    assert result.is_anomaly is True
    assert "temperature_spike" in result.anomaly_types
    assert result.score is not None
    assert result.training_sample_count == 20


def test_engine_detects_power_drops() -> None:
    engine = AnomalyEngine(contamination=0.05, min_training_samples=5)

    result = engine.evaluate(
        make_point(battery_voltage=21, solar_output=25),
        history=[make_point()] * 20,
    )

    assert result.is_anomaly is True
    assert "power_drop" in result.anomaly_types


def test_engine_detects_signal_instability() -> None:
    engine = AnomalyEngine(contamination=0.05, min_training_samples=5)

    result = engine.evaluate(make_point(signal_strength=-105), history=[make_point()] * 20)

    assert result.is_anomaly is True
    assert "signal_instability" in result.anomaly_types


def test_engine_detects_fuel_anomalies() -> None:
    engine = AnomalyEngine(contamination=0.05, min_training_samples=5)

    result = engine.evaluate(make_point(fuel_level=4), history=[make_point()] * 20)

    assert result.is_anomaly is True
    assert "fuel_anomaly" in result.anomaly_types

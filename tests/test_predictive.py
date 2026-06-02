from datetime import datetime, timezone, timedelta

from app.ai.predictive import PredictiveMaintenanceModel
from app.schemas.telemetry import TelemetryCreate


def make_point(ts: datetime, **kwargs) -> TelemetryCreate:
    defaults = dict(
        battery_voltage=27.5,
        solar_output=82.0,
        cpu_temperature=42.0,
        fuel_level=71.0,
        signal_strength=-68.0,
        orientation_pitch=0.0,
        orientation_yaw=0.0,
    )
    defaults.update(kwargs)
    return TelemetryCreate(satellite_id="SAT-PRED", timestamp=ts, **defaults)


def test_forecast_and_risk():
    # create a history where fuel is steadily decreasing
    now = datetime.now(timezone.utc)
    hist = []
    for i in range(30):
        ts = now - timedelta(seconds=(30 - i) * 60)
        fuel = 70.0 - i * 1.5  # drops quickly
        hist.append(make_point(ts, fuel_level=fuel))

    model = PredictiveMaintenanceModel(window_size=5)
    model.train(hist)

    res = model.forecast(hist[-5:], steps=3)
    assert len(res.forecasts) == 3
    # since fuel was decreasing, risk should be elevated
    assert res.maintenance_risk >= 0.8

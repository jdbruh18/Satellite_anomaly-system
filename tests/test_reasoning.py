from app.ai.reasoning import explain_anomaly


def test_explain_temperature_spike():
    features = {"cpu_temperature": 95.0, "battery_voltage": 27.5, "fuel_level": 70.0, "solar_output": 82.0, "signal_strength": -68.0, "orientation_pitch": 0.0, "orientation_yaw": 0.0}
    res = explain_anomaly(features=features, score=-0.6, anomaly_types=["temperature_spike"])
    assert "overheating" in res.probable_cause
    assert res.severity == "CRITICAL"
    assert "Reduce compute load" in res.recommended_action or "thermal" in res.recommended_action


def test_explain_power_drop_warning():
    features = {"cpu_temperature": 42.0, "battery_voltage": 21.0, "fuel_level": 70.0, "solar_output": 25.0, "signal_strength": -68.0, "orientation_pitch": 0.0, "orientation_yaw": 0.0}
    res = explain_anomaly(features=features, score=-0.1, anomaly_types=["power_drop"])
    assert "Battery" in res.probable_cause or "solar" in res.probable_cause
    assert res.severity in ("WARNING", "CRITICAL")


def test_explain_multivariate_outlier():
    features = {"cpu_temperature": 42.0, "battery_voltage": 27.5, "fuel_level": 50.0, "solar_output": 82.0, "signal_strength": -68.0, "orientation_pitch": 0.0, "orientation_yaw": 0.0}
    res = explain_anomaly(features=features, score=-0.25, anomaly_types=["multivariate_outlier"])
    assert "Unusual combination" in res.probable_cause or "Multivariate" in res.explanation
    assert res.severity in ("WARNING", "CRITICAL")

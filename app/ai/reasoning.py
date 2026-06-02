from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ReasoningResult:
    probable_cause: str
    severity: str
    recommended_action: str
    explanation: str


def explain_anomaly(features: Dict[str, float], score: float | None, anomaly_types: List[str]) -> ReasoningResult:
    """Produce a short, human-readable reasoning for an anomaly.

    This function is intentionally rule-based and deterministic so it can run
    offline without contacting external services.
    """
    parts: List[str] = []
    causes: List[str] = []
    actions: List[str] = []
    severity = "INFO"

    # Map domain anomaly types to causes/actions/severity
    if not anomaly_types and (score is None or score >= 0):
        probable = "No anomaly detected"
        return ReasoningResult(
            probable_cause=probable,
            severity="INFO",
            recommended_action="Continue monitoring.",
            explanation="Model did not flag this point as anomalous.",
        )

    if "temperature_spike" in anomaly_types:
        causes.append("CPU or thermal control subsystem overheating")
        actions.append("Reduce compute load, activate thermal mitigation, inspect radiators/thermal sensors")
        severity = "CRITICAL"

    if "fuel_anomaly" in anomaly_types:
        causes.append("Unexpected fuel depletion or leak, or thruster misfire")
        actions.append("Check propulsion telemetry, isolate valves, consider safe mode to conserve fuel")
        severity = "CRITICAL"

    if "power_drop" in anomaly_types:
        causes.append("Battery discharge or solar array underperformance (shadowing or degradation)")
        actions.append("Switch to backup power, check solar arrays and power distribution")
        if severity != "CRITICAL":
            severity = "WARNING"

    if "signal_instability" in anomaly_types:
        causes.append("Antenna misalignment or radio-frequency interference")
        actions.append("Attempt re-pointing, check ground station link and interference sources")
        if severity != "CRITICAL":
            severity = "WARNING"

    if "multivariate_outlier" in anomaly_types:
        causes.append("Unusual combination of telemetry values not seen during training")
        actions.append("Run diagnostic routines and gather more telemetry for analysis")
        if severity != "CRITICAL":
            severity = "WARNING"

    # Score-based adjustments: lower (more negative) decision_function indicates stronger anomaly
    if score is not None:
        if score < -0.5:
            severity = "CRITICAL"
            parts.append(f"Model score {score:.3f} indicates a strong anomaly.")
        elif score < -0.2 and severity != "CRITICAL":
            severity = "WARNING"
            parts.append(f"Model score {score:.3f} indicates a probable anomaly.")
        else:
            parts.append(f"Model score {score:.3f} (lower is more anomalous).")

    probable_cause = "; ".join(causes) if causes else "Uncertain — requires investigation"
    recommended_action = "; ".join(actions) if actions else "Run diagnostics and collect more data."
    explanation = " ".join(parts) if parts else ""

    # Compose human-friendly explanation
    if causes:
        explanation = f"Probable cause(s): {probable_cause}. {explanation}"
    else:
        explanation = explanation or "Anomaly detected — further analysis recommended."

    return ReasoningResult(
        probable_cause=probable_cause,
        severity=severity,
        recommended_action=recommended_action,
        explanation=explanation,
    )

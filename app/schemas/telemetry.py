from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TelemetryCreate(BaseModel):
    satellite_id: str = Field(min_length=1, max_length=64)
    sequence: int | None = Field(default=None, ge=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    battery_voltage: float = Field(ge=0, le=40)
    solar_output: float = Field(ge=0, le=120)
    cpu_temperature: float = Field(ge=-80, le=150)
    fuel_level: float = Field(ge=0, le=100)
    signal_strength: float = Field(ge=-150, le=0)
    orientation_pitch: float = Field(ge=-180, le=180)
    orientation_yaw: float = Field(ge=-180, le=180)

    @field_validator("timestamp")
    @classmethod
    def ensure_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


class TelemetryRead(TelemetryCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnomalyResult(BaseModel):
    is_anomaly: bool
    score: float | None
    reason: str
    severity: str = "INFO"
    explanation: str = ""
    recommended_action: str = ""
    anomaly_types: list[str] = Field(default_factory=list)
    features: dict[str, float]
    training_sample_count: int


class AnomalyEventRead(BaseModel):
    id: int
    telemetry_id: int
    is_anomaly: bool
    score: float | None
    reason: str
    severity: str
    explanation: str
    recommended_action: str
    anomaly_types: list[str]
    features: dict[str, float]
    training_sample_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TelemetryIngestResponse(BaseModel):
    telemetry: TelemetryRead
    anomaly: AnomalyEventRead


class SimulationRequest(BaseModel):
    satellite_id: str = Field(default="SAT-001", min_length=1, max_length=64)
    count: int = Field(default=25, ge=1, le=1000)
    anomaly_rate: float = Field(default=0.05, ge=0, le=1)
    seed: int | None = None


class SimulationResponse(BaseModel):
    satellite_id: str
    inserted: int
    anomalies_detected: int

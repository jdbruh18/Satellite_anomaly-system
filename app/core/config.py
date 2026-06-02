from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Satellite Telemetry Anomaly System"
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"

    database_url: str = Field(
        default="postgresql+asyncpg://telemetry:telemetry@localhost:5432/telemetry"
    )

    anomaly_contamination: float = Field(default=0.05, ge=0.001, le=0.5)
    anomaly_min_training_samples: int = Field(default=30, ge=5)
    anomaly_window_size: int = Field(default=500, ge=30)

    simulator_interval_seconds: float = Field(default=1.0, gt=0)
    simulator_anomaly_rate: float = Field(default=0.05, ge=0, le=1)
    alert_webhook: str | None = Field(default=None)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

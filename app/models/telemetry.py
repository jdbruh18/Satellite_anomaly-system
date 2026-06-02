from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TelemetryPoint(Base):
    __tablename__ = "telemetry_points"
    __table_args__ = (
        Index("ix_telemetry_satellite_timestamp", "satellite_id", "timestamp"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    satellite_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    sequence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    battery_voltage: Mapped[float] = mapped_column(Float, nullable=False)
    solar_output: Mapped[float] = mapped_column(Float, nullable=False)
    cpu_temperature: Mapped[float] = mapped_column(Float, nullable=False)
    fuel_level: Mapped[float] = mapped_column(Float, nullable=False)
    signal_strength: Mapped[float] = mapped_column(Float, nullable=False)
    orientation_pitch: Mapped[float] = mapped_column(Float, nullable=False)
    orientation_yaw: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    anomaly_events: Mapped[list["AnomalyEvent"]] = relationship(
        back_populates="telemetry",
        cascade="all, delete-orphan",
    )


class AnomalyEvent(Base):
    __tablename__ = "anomaly_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telemetry_id: Mapped[int] = mapped_column(
        ForeignKey("telemetry_points.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    is_anomaly: Mapped[bool] = mapped_column(Boolean, index=True, nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    anomaly_types: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    features: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="INFO")
    explanation: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    recommended_action: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    training_sample_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    telemetry: Mapped[TelemetryPoint] = relationship(back_populates="anomaly_events")

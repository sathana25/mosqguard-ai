from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20))  # resident | officer | worker
    password_hash: Mapped[str] = mapped_column(String(200))
    ward: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Ward(Base):
    __tablename__ = "wards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    # Bounding box of the ward
    min_lat: Mapped[float] = mapped_column(Float)
    max_lat: Mapped[float] = mapped_column(Float)
    min_lon: Mapped[float] = mapped_column(Float)
    max_lon: Mapped[float] = mapped_column(Float)
    # Sample conditions, replaced by live data when an API key is configured
    rain_7d_mm: Mapped[float] = mapped_column(Float, default=0)
    dengue_cases_30d: Mapped[int] = mapped_column(Integer, default=0)
    rain_forecast_7d_mm: Mapped[float] = mapped_column(Float, default=0)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    ward_id: Mapped[int] = mapped_column(ForeignKey("wards.id"))
    note: Mapped[str] = mapped_column(Text, default="")
    photo: Mapped[str] = mapped_column(String(200))
    image_hash: Mapped[str] = mapped_column(String(32), default="")

    # AI detection result: {suspected, confidence, objects[], water_visible, larvae_visible, engine, summary}
    detection: Mapped[dict] = mapped_column(JSON, default=dict)
    # Risk result: {score, level, reasons[]}
    risk: Mapped[dict] = mapped_column(JSON, default=dict)
    risk_score: Mapped[int] = mapped_column(Integer, default=0, index=True)

    # open -> assigned -> cleaned -> closed
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)
    confirmations: Mapped[int] = mapped_column(Integer, default=1)
    assigned_to_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    after_photo: Mapped[str | None] = mapped_column(String(200), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cleaned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    reporter: Mapped[User] = relationship(foreign_keys=[reporter_id])
    assigned_to: Mapped[User | None] = relationship(foreign_keys=[assigned_to_id])
    ward: Mapped[Ward] = relationship()

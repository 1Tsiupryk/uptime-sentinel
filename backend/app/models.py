from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, func, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class Monitor(Base):
    __tablename__ = "monitors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    interval_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    enabled: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=True, 
        server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now()
    )
    check_results: Mapped[list["CheckResult"]] = relationship(
        back_populates="monitor",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    incidents: Mapped[list["Incident"]] = relationship(
        back_populates="monitor",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class CheckResult(Base):
    __tablename__ = "check_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    monitor_id: Mapped[int] = mapped_column(
        ForeignKey("monitors.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    monitor: Mapped["Monitor"] = relationship(
        back_populates="check_results"
    )


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    monitor_id: Mapped[int] = mapped_column(
        ForeignKey("monitors.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    opening_check_id: Mapped[int] = mapped_column(
        ForeignKey("check_results.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    closing_check_id: Mapped[int | None] = mapped_column(
        ForeignKey("check_results.id", ondelete="SET NULL"),
        nullable=True,
        unique=True
    )
    monitor: Mapped["Monitor"] = relationship(
        back_populates="incidents",
    )
    opening_check: Mapped["CheckResult"] = relationship(
        foreign_keys=[opening_check_id],
    )
    closing_check: Mapped["CheckResult | None"] = relationship(
        foreign_keys=[closing_check_id],
    )
        
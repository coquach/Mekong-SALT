"""Decision logging model."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import DecisionActorType
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.sqltypes import enum_type


class DecisionLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Audit record for risk, planning, and execution outcomes."""

    __tablename__ = "decision_logs"

    region_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("regions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    risk_assessment_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("risk_assessments.id", ondelete="SET NULL"),
        nullable=True,
    )
    action_plan_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("action_plans.id", ondelete="SET NULL"),
        nullable=True,
    )
    action_execution_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("action_executions.id", ondelete="SET NULL"),
        nullable=True,
    )
    logged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    actor_type: Mapped[DecisionActorType] = mapped_column(
        enum_type(DecisionActorType, "decision_actor_type"),
        nullable=False,
        default=DecisionActorType.SYSTEM,
    )
    actor_name: Mapped[str] = mapped_column(String(255), nullable=False, default="system")
    summary: Mapped[str] = mapped_column(Text(), nullable=False)
    outcome: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    store_as_memory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    region = relationship("Region", back_populates="decision_logs")
    risk_assessment = relationship("RiskAssessment", back_populates="decision_logs")
    action_plan = relationship("ActionPlan", back_populates="decision_logs")
    action_execution = relationship("ActionExecution", back_populates="decision_logs")

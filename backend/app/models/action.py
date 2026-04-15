"""Action plan and execution models."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ActionPlanStatus, ActionType, ExecutionStatus
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.sqltypes import enum_type


class ActionPlan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persisted plan generated from an assessment."""

    __tablename__ = "action_plans"

    region_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("regions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    risk_assessment_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("risk_assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    incident_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[ActionPlanStatus] = mapped_column(
        enum_type(ActionPlanStatus, "action_plan_status"),
        nullable=False,
        default=ActionPlanStatus.DRAFT,
        index=True,
    )
    objective: Mapped[str] = mapped_column(String(255), nullable=False)
    generated_by: Mapped[str] = mapped_column(String(100), nullable=False, default="system")
    model_provider: Mapped[str | None] = mapped_column(String(100), nullable=True)
    summary: Mapped[str] = mapped_column(Text(), nullable=False)
    assumptions: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    plan_steps: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    validation_result: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    region = relationship("Region", back_populates="action_plans")
    risk_assessment = relationship("RiskAssessment", back_populates="action_plans")
    incident = relationship("Incident", back_populates="action_plans")
    approvals = relationship(
        "Approval",
        back_populates="action_plan",
        cascade="all, delete-orphan",
    )
    executions = relationship(
        "ActionExecution",
        back_populates="action_plan",
        cascade="all, delete-orphan",
    )
    execution_batches = relationship(
        "ExecutionBatch",
        back_populates="action_plan",
        cascade="all, delete-orphan",
    )
    decision_logs = relationship("DecisionLog", back_populates="action_plan")
    audit_logs = relationship("AuditLog", back_populates="action_plan")
    agent_runs = relationship("AgentRun", back_populates="action_plan")


class ExecutionBatch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Execution transaction grouping one simulated plan run."""

    __tablename__ = "execution_batches"

    plan_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("action_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    region_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("regions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[ExecutionStatus] = mapped_column(
        enum_type(ExecutionStatus, "execution_status"),
        nullable=False,
        default=ExecutionStatus.PENDING,
        index=True,
    )
    simulated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(120), nullable=True, unique=True)
    requested_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    action_plan = relationship("ActionPlan", back_populates="execution_batches")
    region = relationship("Region", back_populates="execution_batches")
    executions = relationship("ActionExecution", back_populates="execution_batch")


class ActionExecution(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Execution record for a simulated action."""

    __tablename__ = "action_executions"

    plan_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("action_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    batch_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("execution_batches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    region_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("regions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action_type: Mapped[ActionType] = mapped_column(
        enum_type(ActionType, "action_type"),
        nullable=False,
    )
    status: Mapped[ExecutionStatus] = mapped_column(
        enum_type(ExecutionStatus, "execution_status"),
        nullable=False,
        default=ExecutionStatus.PENDING,
        index=True,
    )
    simulated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    step_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    result_summary: Mapped[str | None] = mapped_column(Text(), nullable=True)
    result_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(120), nullable=True, unique=True)
    requested_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    action_plan = relationship("ActionPlan", back_populates="executions")
    execution_batch = relationship("ExecutionBatch", back_populates="executions")
    region = relationship("Region", back_populates="action_executions")
    decision_logs = relationship("DecisionLog", back_populates="action_execution")
    notifications = relationship("Notification", back_populates="execution")
    outcomes = relationship(
        "ActionOutcome",
        back_populates="execution",
        cascade="all, delete-orphan",
    )
    audit_logs = relationship("AuditLog", back_populates="action_execution")

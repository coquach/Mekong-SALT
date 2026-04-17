"""Human approval persistence model."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ApprovalDecision
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.sqltypes import enum_type


class Approval(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Human approval decision recorded before simulated execution."""

    __tablename__ = "approvals"

    plan_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("action_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    decided_by_name: Mapped[str] = mapped_column(String(255), nullable=False)
    decision: Mapped[ApprovalDecision] = mapped_column(
        enum_type(ApprovalDecision, "approval_decision"),
        nullable=False,
        index=True,
    )
    comment: Mapped[str | None] = mapped_column(Text(), nullable=True)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    action_plan = relationship("ActionPlan", back_populates="approvals")

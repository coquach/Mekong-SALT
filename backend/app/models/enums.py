"""Shared enums for persistence models."""

from enum import Enum


class StationStatus(str, Enum):
    """Supported sensor station lifecycle states."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class RiskLevel(str, Enum):
    """Deterministic risk levels for salinity intrusion."""

    SAFE = "safe"
    WARNING = "warning"
    DANGER = "danger"
    CRITICAL = "critical"


class TrendDirection(str, Enum):
    """Observed or inferred trend direction."""

    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"
    UNKNOWN = "unknown"


class AlertStatus(str, Enum):
    """Alert lifecycle states."""

    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class ActionPlanStatus(str, Enum):
    """Action plan lifecycle states."""

    DRAFT = "draft"
    VALIDATED = "validated"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SIMULATED = "simulated"
    CLOSED = "closed"


class ActionType(str, Enum):
    """Allowed simulated action types for the MVP."""

    CLOSE_GATE = "close_gate"
    OPEN_GATE = "open_gate"
    START_PUMP = "start_pump"
    STOP_PUMP = "stop_pump"
    SEND_ALERT = "send_alert"
    NOTIFY_FARMERS = "notify-farmers"
    WAIT_SAFE_WINDOW = "wait-safe-window"
    CLOSE_GATE_SIMULATED = "close-gate-simulated"
    START_PUMP_SIMULATED = "start-pump-simulated"


class ExecutionStatus(str, Enum):
    """Execution states for simulated action runs."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DocumentStatus(str, Enum):
    """Knowledge document lifecycle states."""

    ACTIVE = "active"
    ARCHIVED = "archived"


class DecisionActorType(str, Enum):
    """Actor type that produced a decision log record."""

    SYSTEM = "system"
    OPERATOR = "operator"
    AGENT = "agent"


class IncidentStatus(str, Enum):
    """Incident lifecycle states."""

    OPEN = "open"
    INVESTIGATING = "investigating"
    PENDING_PLAN = "pending_plan"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    EXECUTING = "executing"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ApprovalDecision(str, Enum):
    """Human approval decisions for action plans."""

    APPROVED = "approved"
    REJECTED = "rejected"


class NotificationChannel(str, Enum):
    """Supported notification channels."""

    DASHBOARD = "dashboard"
    SMS_MOCK = "sms_mock"
    ZALO_MOCK = "zalo_mock"
    EMAIL_MOCK = "email_mock"


class NotificationStatus(str, Enum):
    """Notification delivery states."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class AuditEventType(str, Enum):
    """Common audit event categories."""

    AUTH = "auth"
    INGESTION = "ingestion"
    RISK = "risk"
    INCIDENT = "incident"
    PLAN = "plan"
    APPROVAL = "approval"
    EXECUTION = "execution"
    NOTIFICATION = "notification"
    KNOWLEDGE = "knowledge"


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
    SIMULATED = "simulated"
    CLOSED = "closed"


class ActionType(str, Enum):
    """Allowed simulated action types for the MVP."""

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


"""Notification channel wrappers.

This module re-exports the current implementation without logic changes.
"""

from app.services.notification_service import (
    create_execution_alert_notifications,
    create_execution_summary_notifications,
    create_incident_created_notifications,
    create_notification,
    create_operational_notifications,
    create_plan_created_notifications,
    list_notifications,
    mark_notification_read,
)

__all__ = [
    "create_notification",
    "create_execution_alert_notifications",
    "create_operational_notifications",
    "create_incident_created_notifications",
    "create_plan_created_notifications",
    "create_execution_summary_notifications",
    "list_notifications",
    "mark_notification_read",
]

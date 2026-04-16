"""Notification domain service package.

Thin wrappers to preserve behavior while moving toward explicit boundaries.
"""

from app.services.notify.channels import (
    create_execution_alert_notifications,
    create_execution_summary_notifications,
    create_incident_created_notifications,
    create_notification,
    create_operational_notifications,
    create_plan_created_notifications,
    get_domain_event_notification_dispatcher,
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
    "get_domain_event_notification_dispatcher",
    "list_notifications",
    "mark_notification_read",
]

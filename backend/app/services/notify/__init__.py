"""Notification domain service package.

Thin wrappers to preserve behavior while moving toward explicit boundaries.
"""

from app.services.notify.channels import (
    create_notification,
    create_operational_notifications,
    get_domain_event_notification_dispatcher,
    list_notifications,
    mark_notification_read,
)

__all__ = [
    "create_notification",
    "create_operational_notifications",
    "get_domain_event_notification_dispatcher",
    "list_notifications",
    "mark_notification_read",
]

"""Notification channel wrappers.

This module re-exports the current implementation without logic changes.
"""

from app.services.notification_service import (
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

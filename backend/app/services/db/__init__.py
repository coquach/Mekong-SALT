"""Persistence-focused domain service package.

Thin wrappers to preserve behavior while moving toward explicit boundaries.
"""

from app.services.db.domain_events import (
    DomainEventNotificationDispatcher,
    append_domain_event,
    append_domain_event_and_dispatch,
    list_domain_events_after_cursor,
    to_stream_event_payload,
)

__all__ = [
    "DomainEventNotificationDispatcher",
    "append_domain_event",
    "append_domain_event_and_dispatch",
    "list_domain_events_after_cursor",
    "to_stream_event_payload",
]

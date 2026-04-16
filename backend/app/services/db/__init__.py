"""Persistence-focused domain service package.

Thin wrappers to preserve behavior while moving toward explicit boundaries.
"""

from app.services.db.domain_events import (
    append_domain_event,
    list_domain_events_after_cursor,
    to_stream_event_payload,
)

__all__ = [
    "append_domain_event",
    "list_domain_events_after_cursor",
    "to_stream_event_payload",
]

"""Domain event persistence wrappers.

This module re-exports the current implementation without logic changes.
"""

from app.services.domain_event_service import (
    append_domain_event,
    list_domain_events_after_cursor,
    to_stream_event_payload,
)

__all__ = [
    "append_domain_event",
    "list_domain_events_after_cursor",
    "to_stream_event_payload",
]

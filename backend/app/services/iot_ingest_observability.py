"""Shared ingest observability helpers for MQTT and Pub/Sub workers."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import threading
from typing import Any

from app.core.config import Settings

UTC = timezone.utc

_lock = threading.Lock()
_metrics_store: dict[str, dict[str, Any]] = {
    "mqtt": {
        "received_messages": 0,
        "status_messages": 0,
        "ingested_success": 0,
        "parse_failures": 0,
        "persist_failures": 0,
        "dead_letter_published": 0,
        "dead_letter_archived": 0,
        "last_error": None,
        "updated_at": None,
    },
    "pubsub": {
        "received_messages": 0,
        "ingested_success": 0,
        "parse_failures": 0,
        "persist_failures": 0,
        "dead_letter_published": 0,
        "dead_letter_archived": 0,
        "nack_retries": 0,
        "delivery_attempt_exceeded": 0,
        "queue_lag_seconds_last": None,
        "queue_lag_seconds_max": 0.0,
        "queue_lag_seconds_total": 0.0,
        "queue_lag_samples": 0,
        "last_error": None,
        "updated_at": None,
    },
}


def set_worker_metrics(worker: str, metrics: dict[str, Any]) -> None:
    """Replace one worker metric snapshot atomically."""
    now = datetime.now(UTC).isoformat()
    with _lock:
        entry = _metrics_store.setdefault(worker, {})
        entry.update(metrics)
        entry["updated_at"] = now


def update_worker_metric(worker: str, **values: Any) -> None:
    """Patch selected metric values for one worker."""
    now = datetime.now(UTC).isoformat()
    with _lock:
        entry = _metrics_store.setdefault(worker, {})
        entry.update(values)
        entry["updated_at"] = now


def record_queue_lag(worker: str, lag_seconds: float) -> None:
    """Update queue lag aggregates."""
    now = datetime.now(UTC).isoformat()
    lag = max(0.0, float(lag_seconds))
    with _lock:
        entry = _metrics_store.setdefault(worker, {})
        current_max = float(entry.get("queue_lag_seconds_max") or 0.0)
        total = float(entry.get("queue_lag_seconds_total") or 0.0)
        samples = int(entry.get("queue_lag_samples") or 0)
        entry["queue_lag_seconds_last"] = lag
        entry["queue_lag_seconds_max"] = max(current_max, lag)
        entry["queue_lag_seconds_total"] = total + lag
        entry["queue_lag_samples"] = samples + 1
        entry["updated_at"] = now


def get_ingest_metrics_snapshot() -> dict[str, Any]:
    """Return a deep-copied snapshot for API responses."""
    with _lock:
        payload = deepcopy(_metrics_store)

    pubsub = payload.get("pubsub", {})
    samples = int(pubsub.get("queue_lag_samples") or 0)
    total = float(pubsub.get("queue_lag_seconds_total") or 0.0)
    pubsub["queue_lag_seconds_avg"] = round(total / samples, 3) if samples > 0 else None
    return payload


def archive_dead_letter(
    *,
    settings: Settings,
    source: str,
    reason: str,
    payload_raw: str,
    metadata: dict[str, Any] | None = None,
) -> bool:
    """Append one dead-letter record to archive sink when enabled."""
    if not getattr(settings, "iot_dlq_archive_enabled", True):
        return False

    archive_path = Path(getattr(settings, "iot_dlq_archive_path", "artifacts/ingest_dlq_archive.jsonl"))
    if not archive_path.is_absolute():
        archive_path = Path.cwd() / archive_path

    record = {
        "archived_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "source": source,
        "reason": reason,
        "payload": payload_raw,
        "metadata": metadata or {},
    }
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=True)
    with _lock:
        with archive_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    return True

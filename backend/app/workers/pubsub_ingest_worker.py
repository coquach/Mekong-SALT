"""Pub/Sub subscriber worker for cloud sensor ingestion."""

from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import logging
import os
from typing import Any

from google.cloud import pubsub_v1
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.db.session import AsyncSessionFactory, close_database_engine
from app.schemas.pubsub import PubSubSensorReadingEvent
from app.schemas.sensor import SensorReadingIngestRequest
from app.services.iot_ingest_observability import (
    archive_dead_letter,
    record_queue_lag,
    set_worker_metrics,
    update_worker_metric,
)
from app.services.sensor_service import ingest_sensor_reading

logger = logging.getLogger(__name__)
UTC = timezone.utc


@dataclass(slots=True)
class PubSubIngestMetrics:
    """Runtime counters for Pub/Sub ingestion observability."""

    received_messages: int = 0
    ingested_success: int = 0
    parse_failures: int = 0
    persist_failures: int = 0
    dead_letter_published: int = 0
    dead_letter_archived: int = 0
    nack_retries: int = 0
    delivery_attempt_exceeded: int = 0


class PubSubIngestWorker:
    """Consumes Pub/Sub messages and forwards valid readings to ingest service."""

    def __init__(self, *, settings: Settings, loop: asyncio.AbstractEventLoop) -> None:
        self._settings = settings
        self._loop = loop
        self._metrics = PubSubIngestMetrics()
        self._stopping = False
        self._subscriber = pubsub_v1.SubscriberClient()
        self._publisher = pubsub_v1.PublisherClient()
        self._streaming_pull_future: pubsub_v1.subscriber.futures.StreamingPullFuture | None = None
        self._stopped = asyncio.Event()
        set_worker_metrics("pubsub", asdict(self._metrics))

    async def run(self) -> None:
        """Subscribe and process messages until cancelled or fatal stop."""
        project_id = self._settings.pubsub_project_id
        subscription = self._settings.pubsub_subscription_sensor_readings
        if not project_id or not subscription:
            raise RuntimeError("Pub/Sub ingest requires PUBSUB_PROJECT_ID and PUBSUB_SUBSCRIPTION_SENSOR_READINGS.")

        emulator_host = self._settings.pubsub_emulator_host
        if emulator_host:
            os.environ.setdefault("PUBSUB_EMULATOR_HOST", emulator_host)

        sub_path = self._subscriber.subscription_path(project_id, subscription)
        flow_control = pubsub_v1.types.FlowControl(
            max_messages=max(1, self._settings.pubsub_flow_max_messages),
        )

        logger.info(
            "Pub/Sub ingest worker subscribing",
            extra={
                "subscription": sub_path,
                "flow_max_messages": self._settings.pubsub_flow_max_messages,
            },
        )
        self._streaming_pull_future = self._subscriber.subscribe(
            sub_path,
            callback=self._on_message,
            flow_control=flow_control,
        )

        try:
            await self._stopped.wait()
        finally:
            future = self._streaming_pull_future
            if future is not None:
                future.cancel()
            self._subscriber.close()
            self._publisher.close()
            logger.info("Pub/Sub ingest worker counters", extra=asdict(self._metrics))

    def stop(self) -> None:
        """Request worker shutdown."""
        self._stopping = True
        future = self._streaming_pull_future
        if future is not None:
            future.cancel()
        self._loop.call_soon_threadsafe(self._stopped.set)

    def _on_message(self, message: pubsub_v1.subscriber.message.Message) -> None:
        payload_raw = message.data.decode("utf-8", errors="replace")
        publish_time = message.publish_time
        lag_seconds = 0.0
        if publish_time is not None:
            if publish_time.tzinfo is None:
                publish_time = publish_time.replace(tzinfo=UTC)
            lag_seconds = max(0.0, (datetime.now(UTC) - publish_time).total_seconds())
            record_queue_lag("pubsub", lag_seconds)

        future = asyncio.run_coroutine_threadsafe(
            self._handle_message(
                message=message,
                payload_raw=payload_raw,
                lag_seconds=lag_seconds,
            ),
            self._loop,
        )
        future.add_done_callback(self._log_future_exception)

    @staticmethod
    def _log_future_exception(future: asyncio.Future[Any]) -> None:
        try:
            future.result()
        except Exception:
            logger.exception("Pub/Sub message handler failed")

    async def _handle_message(
        self,
        *,
        message: pubsub_v1.subscriber.message.Message,
        payload_raw: str,
        lag_seconds: float,
    ) -> None:
        self._metrics.received_messages += 1
        self._sync_metrics()

        try:
            payload = json.loads(payload_raw)
            if not isinstance(payload, dict):
                raise ValueError("Pub/Sub sensor payload must be a JSON object.")
            event = PubSubSensorReadingEvent.model_validate(payload)
            mapped_payload = event.to_ingest_payload(
                pubsub_meta={
                    "message_id": message.message_id,
                    "publish_time": message.publish_time.isoformat() if message.publish_time else None,
                    "attributes": dict(message.attributes or {}),
                },
            )
            request_payload = SensorReadingIngestRequest.model_validate(mapped_payload)
        except (json.JSONDecodeError, ValidationError, ValueError) as exc:
            self._metrics.parse_failures += 1
            update_worker_metric("pubsub", last_error=str(exc))
            await self._send_to_dead_letter(
                source_message=message,
                payload_raw=payload_raw,
                reason=str(exc),
                lag_seconds=lag_seconds,
            )
            message.ack()
            self._sync_metrics()
            return

        try:
            async with AsyncSessionFactory() as session:
                await ingest_sensor_reading(session, request_payload)
        except Exception as exc:
            self._metrics.persist_failures += 1
            update_worker_metric("pubsub", last_error=str(exc))
            delivery_attempt = int(getattr(message, "delivery_attempt", 0) or 0)
            max_attempts = max(1, int(self._settings.pubsub_max_delivery_attempts))
            if delivery_attempt < max_attempts:
                self._metrics.nack_retries += 1
                self._sync_metrics()
                message.nack()
                return

            self._metrics.delivery_attempt_exceeded += 1
            await self._send_to_dead_letter(
                source_message=message,
                payload_raw=payload_raw,
                reason=f"persist_failure_exhausted_retries: {exc}",
                lag_seconds=lag_seconds,
            )
            message.ack()
            self._sync_metrics()
            return

        self._metrics.ingested_success += 1
        self._sync_metrics()
        message.ack()

    async def _send_to_dead_letter(
        self,
        *,
        source_message: pubsub_v1.subscriber.message.Message,
        payload_raw: str,
        reason: str,
        lag_seconds: float,
    ) -> None:
        dead_letter_topic = self._settings.pubsub_dead_letter_topic
        metadata = {
            "message_id": source_message.message_id,
            "delivery_attempt": int(getattr(source_message, "delivery_attempt", 0) or 0),
            "lag_seconds": round(lag_seconds, 3),
        }

        if dead_letter_topic and self._settings.pubsub_project_id:
            topic_path = self._publisher.topic_path(self._settings.pubsub_project_id, dead_letter_topic)
            envelope = {
                "failed_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
                "reason": reason,
                "payload": payload_raw,
                "metadata": metadata,
            }
            publish_future = self._publisher.publish(
                topic_path,
                json.dumps(envelope, ensure_ascii=True).encode("utf-8"),
            )
            try:
                await asyncio.wrap_future(publish_future)
                self._metrics.dead_letter_published += 1
            except Exception:
                logger.exception("Failed to publish Pub/Sub dead-letter payload")

        archived = archive_dead_letter(
            settings=self._settings,
            source="pubsub",
            reason=reason,
            payload_raw=payload_raw,
            metadata=metadata,
        )
        if archived:
            self._metrics.dead_letter_archived += 1

    def _sync_metrics(self) -> None:
        set_worker_metrics("pubsub", asdict(self._metrics))


def start_pubsub_ingest_worker(*, settings: Settings | None = None) -> asyncio.Task[None]:
    """Start Pub/Sub ingest loop as a background task."""
    resolved_settings = settings or get_settings()
    return asyncio.create_task(
        pubsub_ingest_loop(settings=resolved_settings),
        name="pubsub-ingest-worker",
    )


async def pubsub_ingest_loop(*, settings: Settings | None = None) -> None:
    """Run Pub/Sub ingestion loop with reconnect backoff."""
    resolved_settings = settings or get_settings()
    backoff_seconds = 1.0
    logger.info("Pub/Sub ingest worker started")

    while True:
        worker = PubSubIngestWorker(settings=resolved_settings, loop=asyncio.get_running_loop())
        try:
            await worker.run()
            backoff_seconds = 1.0
        except asyncio.CancelledError:
            worker.stop()
            logger.info("Pub/Sub ingest worker cancellation requested")
            raise
        except Exception:
            logger.exception(
                "Pub/Sub ingest loop failed; restarting with backoff",
                extra={"backoff_seconds": backoff_seconds},
            )
            await asyncio.sleep(backoff_seconds)
            backoff_seconds = min(backoff_seconds * 2, 30.0)


async def main() -> None:
    """Run Pub/Sub ingest worker as a standalone process."""
    try:
        await pubsub_ingest_loop(settings=get_settings())
    finally:
        await close_database_engine()


if __name__ == "__main__":
    asyncio.run(main())

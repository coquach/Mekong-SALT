"""MQTT subscriber worker for edge sensor ingestion."""

from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import logging
from typing import Any

import paho.mqtt.client as mqtt
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.db.session import AsyncSessionFactory, close_database_engine
from app.schemas.sensor import SensorReadingIngestRequest
from app.services.iot_ingest_observability import (
    archive_dead_letter,
    set_worker_metrics,
    update_worker_metric,
)
from app.services.sensor_service import ingest_sensor_reading

logger = logging.getLogger(__name__)
UTC = timezone.utc


@dataclass(slots=True)
class MqttIngestMetrics:
    """Runtime counters for MQTT ingestion observability."""

    received_messages: int = 0
    status_messages: int = 0
    ingested_success: int = 0
    parse_failures: int = 0
    persist_failures: int = 0
    dead_letter_published: int = 0


class MqttIngestWorker:
    """Consumes MQTT messages and forwards valid readings to existing ingest service."""

    def __init__(self, *, settings: Settings, loop: asyncio.AbstractEventLoop) -> None:
        self._settings = settings
        self._loop = loop
        self._metrics = MqttIngestMetrics()
        self._connected = asyncio.Event()
        self._disconnected = asyncio.Event()
        self._disconnect_reason_code: int | None = None
        self._stopping = False
        self._client = self._build_client()
        set_worker_metrics("mqtt", asdict(self._metrics))

    def _build_client(self) -> mqtt.Client:
        client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=self._settings.mqtt_client_id,
            protocol=mqtt.MQTTv311,
        )
        if self._settings.mqtt_username:
            password = (
                self._settings.mqtt_password.get_secret_value()
                if self._settings.mqtt_password is not None
                else None
            )
            client.username_pw_set(self._settings.mqtt_username, password)
        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.on_message = self._on_message
        return client

    async def run(self) -> None:
        """Connect, subscribe, and keep handling messages until disconnected."""
        logger.info(
            "MQTT ingest worker connecting",
            extra={
                "broker": self._settings.mqtt_broker_url,
                "port": self._settings.mqtt_broker_port,
                "topic_sensor_readings": self._settings.mqtt_topic_sensor_readings,
                "topic_status": self._settings.mqtt_topic_device_status,
            },
        )
        self._client.connect(
            host=self._settings.mqtt_broker_url,
            port=self._settings.mqtt_broker_port,
            keepalive=60,
        )
        self._client.loop_start()
        try:
            await asyncio.wait_for(self._connected.wait(), timeout=15)
            await self._disconnected.wait()
            if not self._stopping:
                raise RuntimeError(
                    f"MQTT worker disconnected unexpectedly (rc={self._disconnect_reason_code})."
                )
        finally:
            self._client.loop_stop()
            if self._client.is_connected():
                self._client.disconnect()
            logger.info("MQTT ingest worker counters", extra=asdict(self._metrics))

    def stop(self) -> None:
        """Request worker shutdown."""
        self._stopping = True
        try:
            if self._client.is_connected():
                self._client.disconnect()
        finally:
            self._loop.call_soon_threadsafe(self._disconnected.set)

    def _on_connect(
        self,
        client: mqtt.Client,
        _userdata: Any,
        _flags: mqtt.ConnectFlags,
        reason_code: mqtt.ReasonCode,
        _properties: mqtt.Properties | None,
    ) -> None:
        rc = int(reason_code)
        if rc != 0:
            logger.error("MQTT connect failed", extra={"reason_code": rc})
            self._disconnect_reason_code = rc
            self._loop.call_soon_threadsafe(self._disconnected.set)
            return

        subscriptions = [
            (self._settings.mqtt_topic_sensor_readings, self._settings.mqtt_qos),
            (self._settings.mqtt_topic_device_status, self._settings.mqtt_qos),
        ]
        subscribe_result, _mid = client.subscribe(subscriptions)
        if subscribe_result != mqtt.MQTT_ERR_SUCCESS:
            logger.error(
                "MQTT subscribe failed",
                extra={"subscribe_result": subscribe_result},
            )
            self._disconnect_reason_code = subscribe_result
            self._loop.call_soon_threadsafe(self._disconnected.set)
            return

        logger.info("MQTT ingest worker subscribed", extra={"subscriptions": subscriptions})
        self._loop.call_soon_threadsafe(self._connected.set)

    def _on_disconnect(
        self,
        _client: mqtt.Client,
        _userdata: Any,
        _disconnect_flags: mqtt.DisconnectFlags,
        reason_code: mqtt.ReasonCode,
        _properties: mqtt.Properties | None,
    ) -> None:
        self._disconnect_reason_code = int(reason_code)
        if not self._stopping and self._disconnect_reason_code != 0:
            logger.warning(
                "MQTT broker disconnected",
                extra={"reason_code": self._disconnect_reason_code},
            )
        self._loop.call_soon_threadsafe(self._disconnected.set)

    def _on_message(
        self,
        _client: mqtt.Client,
        _userdata: Any,
        message: mqtt.MQTTMessage,
    ) -> None:
        payload_raw = message.payload.decode("utf-8", errors="replace")
        future = asyncio.run_coroutine_threadsafe(
            self._handle_message(
                topic=message.topic,
                payload_raw=payload_raw,
                qos=message.qos,
                retain=bool(message.retain),
            ),
            self._loop,
        )
        future.add_done_callback(self._log_future_exception)

    @staticmethod
    def _log_future_exception(future: asyncio.Future[Any]) -> None:
        try:
            future.result()
        except Exception:
            logger.exception("MQTT message handler failed")

    async def _handle_message(
        self,
        *,
        topic: str,
        payload_raw: str,
        qos: int,
        retain: bool,
    ) -> None:
        self._metrics.received_messages += 1
        self._sync_metrics()

        if topic == self._settings.mqtt_topic_device_status:
            self._metrics.status_messages += 1
            self._sync_metrics()
            await self._handle_device_status_message(payload_raw=payload_raw)
            return

        if topic != self._settings.mqtt_topic_sensor_readings:
            logger.warning("Skipping MQTT message from unknown topic", extra={"topic": topic})
            return

        try:
            payload = json.loads(payload_raw)
            if not isinstance(payload, dict):
                raise ValueError("MQTT sensor payload must be a JSON object.")
            mapped_payload = self._map_reading_payload(
                payload=payload,
                mqtt_meta={"topic": topic, "qos": qos, "retain": retain},
            )
            request_payload = SensorReadingIngestRequest.model_validate(mapped_payload)
        except (json.JSONDecodeError, ValidationError, ValueError) as exc:
            self._metrics.parse_failures += 1
            update_worker_metric("mqtt", last_error=str(exc))
            logger.warning("MQTT sensor payload rejected", extra={"reason": str(exc)})
            self._publish_dead_letter(topic=topic, payload_raw=payload_raw, reason=str(exc))
            return

        try:
            async with AsyncSessionFactory() as session:
                await ingest_sensor_reading(session, request_payload)
        except Exception as exc:
            self._metrics.persist_failures += 1
            update_worker_metric("mqtt", last_error=str(exc))
            logger.exception("MQTT sensor payload failed during persistence")
            self._publish_dead_letter(topic=topic, payload_raw=payload_raw, reason=str(exc))
            return

        self._metrics.ingested_success += 1
        self._sync_metrics()
        if self._metrics.received_messages % 20 == 0:
            logger.info("MQTT ingest counters", extra=asdict(self._metrics))

    async def _handle_device_status_message(self, *, payload_raw: str) -> None:
        try:
            payload = json.loads(payload_raw)
        except json.JSONDecodeError:
            logger.warning("MQTT device status payload is not valid JSON")
            return
        if not isinstance(payload, dict):
            logger.warning("MQTT device status payload must be JSON object")
            return
        logger.info("MQTT device status received", extra={"payload": payload})

    def _map_reading_payload(
        self,
        *,
        payload: dict[str, Any],
        mqtt_meta: dict[str, Any],
    ) -> dict[str, Any]:
        station_code = payload.get("station_code") or payload.get("stationCode")
        recorded_at = (
            payload.get("recorded_at")
            or payload.get("recordedAt")
            or datetime.now(UTC).replace(microsecond=0).isoformat()
        )
        source_event_id = (
            payload.get("source_event_id")
            or payload.get("sourceEventId")
            or payload.get("event_id")
            or payload.get("eventId")
        )

        context_payload = payload.get("context_payload") or payload.get("contextPayload")
        if context_payload is None:
            context_payload = {}
        if not isinstance(context_payload, dict):
            context_payload = {"raw_context": context_payload}
        context_payload["mqtt"] = mqtt_meta
        if source_event_id is not None:
            context_payload["source_event_id"] = str(source_event_id)

        mapped: dict[str, Any] = {
            "station_code": station_code,
            "recorded_at": recorded_at,
            "salinity_dsm": (
                payload.get("salinity_dsm")
                or payload.get("salinityDsM")
                or payload.get("salinity")
            ),
            "salinity_gl": payload.get("salinity_gl") or payload.get("salinityGL"),
            "water_level_m": (
                payload.get("water_level_m")
                or payload.get("waterLevelM")
                or payload.get("water_level")
            ),
            "wind_speed_mps": payload.get("wind_speed_mps") or payload.get("windSpeedMps"),
            "wind_direction_deg": payload.get("wind_direction_deg") or payload.get("windDirectionDeg"),
            "flow_rate_m3s": payload.get("flow_rate_m3s") or payload.get("flowRateM3s"),
            "temperature_c": payload.get("temperature_c") or payload.get("temperatureC"),
            "battery_level_pct": payload.get("battery_level_pct") or payload.get("batteryLevelPct"),
            "source": payload.get("source") or "mqtt-edge",
            "context_payload": context_payload,
        }
        return mapped

    def _publish_dead_letter(self, *, topic: str, payload_raw: str, reason: str) -> None:
        message = {
            "failed_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
            "source_topic": topic,
            "reason": reason,
            "payload": payload_raw,
        }
        publish_info = self._client.publish(
            self._settings.mqtt_topic_dead_letter,
            payload=json.dumps(message, ensure_ascii=True),
            qos=min(self._settings.mqtt_qos, 1),
            retain=False,
        )
        if publish_info.rc == mqtt.MQTT_ERR_SUCCESS:
            self._metrics.dead_letter_published += 1
            archived = archive_dead_letter(
                settings=self._settings,
                source="mqtt",
                reason=reason,
                payload_raw=payload_raw,
                metadata={
                    "source_topic": topic,
                    "dead_letter_topic": self._settings.mqtt_topic_dead_letter,
                },
            )
            if archived:
                update_worker_metric(
                    "mqtt",
                    dead_letter_archived=int(self._metrics.dead_letter_published),
                )
            self._sync_metrics()
            return
        logger.error(
            "Failed to publish MQTT dead-letter payload",
            extra={"dead_letter_topic": self._settings.mqtt_topic_dead_letter},
        )

    def _sync_metrics(self) -> None:
        set_worker_metrics("mqtt", asdict(self._metrics))


def start_mqtt_ingest_worker(*, settings: Settings | None = None) -> asyncio.Task[None]:
    """Start MQTT ingest loop as a background task."""
    resolved_settings = settings or get_settings()
    return asyncio.create_task(
        mqtt_ingest_loop(settings=resolved_settings),
        name="mqtt-ingest-worker",
    )


async def mqtt_ingest_loop(*, settings: Settings | None = None) -> None:
    """Run MQTT ingestion loop with reconnect backoff."""
    resolved_settings = settings or get_settings()
    backoff_seconds = 1.0
    logger.info("MQTT ingest worker started")

    while True:
        worker = MqttIngestWorker(settings=resolved_settings, loop=asyncio.get_running_loop())
        try:
            await worker.run()
            backoff_seconds = 1.0
        except asyncio.CancelledError:
            worker.stop()
            logger.info("MQTT ingest worker cancellation requested")
            raise
        except Exception:
            logger.exception(
                "MQTT ingest loop failed; restarting with backoff",
                extra={"backoff_seconds": backoff_seconds},
            )
            await asyncio.sleep(backoff_seconds)
            backoff_seconds = min(backoff_seconds * 2, 30.0)


async def main() -> None:
    """Run MQTT ingest worker as a standalone process."""
    try:
        await mqtt_ingest_loop(settings=get_settings())
    finally:
        await close_database_engine()


if __name__ == "__main__":
    asyncio.run(main())

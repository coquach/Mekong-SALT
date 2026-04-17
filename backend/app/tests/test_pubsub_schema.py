"""Tests for Pub/Sub event contract normalization."""

from datetime import datetime

from app.schemas.pubsub import PubSubSensorReadingEvent


def test_pubsub_event_normalizes_camel_case_fields():
    event = PubSubSensorReadingEvent.model_validate(
        {
            "stationCode": "ST-01",
            "recordedAt": "2026-04-17T11:00:00Z",
            "salinity": "3.90",
            "waterLevelM": "1.42",
            "temperatureC": "29.10",
            "batteryLevelPct": "88.00",
            "eventId": "evt-001",
            "contextPayload": "edge-gateway",
        }
    )
    payload = event.to_ingest_payload(
        pubsub_meta={
            "message_id": "msg-001",
            "publish_time": "2026-04-17T11:00:01+00:00",
            "attributes": {"device": "gw-01"},
        }
    )

    assert payload["station_code"] == "ST-01"
    assert payload["salinity_dsm"] == event.salinity_dsm
    assert payload["water_level_m"] == event.water_level_m
    assert payload["source"] == "pubsub-edge"
    assert payload["context_payload"]["pubsub"]["message_id"] == "msg-001"
    assert payload["context_payload"]["source_event_id"] == "evt-001"
    assert payload["context_payload"]["raw_context"] == "edge-gateway"


def test_pubsub_event_falls_back_to_message_id_and_current_timestamp():
    event = PubSubSensorReadingEvent.model_validate(
        {
            "station_code": "ST-02",
            "salinity_dsm": "2.80",
            "water_level_m": "1.10",
            "source": "custom-pubsub-source",
        }
    )
    payload = event.to_ingest_payload(
        pubsub_meta={
            "message_id": "msg-002",
            "publish_time": None,
            "attributes": {},
        }
    )

    assert payload["source"] == "custom-pubsub-source"
    assert payload["context_payload"]["source_event_id"] == "msg-002"
    # Ensure method always emits an ISO datetime string even when input omitted it.
    datetime.fromisoformat(payload["recorded_at"].replace("Z", "+00:00"))

"""Schemas for Pub/Sub ingest payload contracts."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class PubSubSensorReadingEvent(BaseModel):
    """Canonical Pub/Sub sensor-reading event parsed from cloud payloads."""

    model_config = ConfigDict(extra="ignore")

    station_code: str = Field(
        min_length=1,
        max_length=50,
        validation_alias=AliasChoices("station_code", "stationCode"),
    )
    recorded_at: datetime | None = Field(
        default=None,
        validation_alias=AliasChoices("recorded_at", "recordedAt"),
    )
    salinity_dsm: Decimal | None = Field(
        default=None,
        validation_alias=AliasChoices("salinity_dsm", "salinityDsM", "salinity"),
    )
    salinity_gl: Decimal | None = Field(
        default=None,
        validation_alias=AliasChoices("salinity_gl", "salinityGL"),
    )
    water_level_m: Decimal = Field(
        validation_alias=AliasChoices("water_level_m", "waterLevelM", "water_level")
    )
    wind_speed_mps: Decimal | None = Field(
        default=None,
        validation_alias=AliasChoices("wind_speed_mps", "windSpeedMps"),
    )
    wind_direction_deg: int | None = Field(
        default=None,
        validation_alias=AliasChoices("wind_direction_deg", "windDirectionDeg"),
    )
    flow_rate_m3s: Decimal | None = Field(
        default=None,
        validation_alias=AliasChoices("flow_rate_m3s", "flowRateM3s"),
    )
    temperature_c: Decimal | None = Field(
        default=None,
        validation_alias=AliasChoices("temperature_c", "temperatureC"),
    )
    battery_level_pct: Decimal | None = Field(
        default=None,
        validation_alias=AliasChoices("battery_level_pct", "batteryLevelPct"),
    )
    source_event_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "source_event_id",
            "sourceEventId",
            "event_id",
            "eventId",
        ),
    )
    source: str | None = None
    context_payload: Any | None = Field(
        default=None,
        validation_alias=AliasChoices("context_payload", "contextPayload"),
    )

    def to_ingest_payload(self, *, pubsub_meta: dict[str, Any]) -> dict[str, Any]:
        """Map event payload into canonical ingest request shape."""
        if isinstance(self.context_payload, dict):
            context_payload = dict(self.context_payload)
        elif self.context_payload is None:
            context_payload = {}
        else:
            context_payload = {"raw_context": self.context_payload}

        context_payload["pubsub"] = pubsub_meta
        if self.source_event_id is not None:
            context_payload["source_event_id"] = str(self.source_event_id)
        elif pubsub_meta.get("message_id") is not None:
            context_payload["source_event_id"] = str(pubsub_meta["message_id"])

        return {
            "station_code": self.station_code,
            "recorded_at": (
                self.recorded_at or datetime.now(UTC).replace(microsecond=0)
            ).isoformat(),
            "salinity_dsm": self.salinity_dsm,
            "salinity_gl": self.salinity_gl,
            "water_level_m": self.water_level_m,
            "wind_speed_mps": self.wind_speed_mps,
            "wind_direction_deg": self.wind_direction_deg,
            "flow_rate_m3s": self.flow_rate_m3s,
            "temperature_c": self.temperature_c,
            "battery_level_pct": self.battery_level_pct,
            "source": self.source or "pubsub-edge",
            "context_payload": context_payload,
        }

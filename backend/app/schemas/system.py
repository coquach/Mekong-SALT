"""System-level schemas."""

from pydantic import BaseModel, ConfigDict


class HealthPayload(BaseModel):
    """Health endpoint payload."""

    model_config = ConfigDict(extra="forbid")

    service: str
    version: str
    environment: str
    dependencies: dict[str, str]


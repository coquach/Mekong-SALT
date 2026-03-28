"""Common API response schemas."""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ResponseMeta(BaseModel):
    """Metadata returned with every API response."""

    model_config = ConfigDict(extra="forbid")

    request_id: str | None = None
    timestamp: datetime


class ErrorDetail(BaseModel):
    """Structured error information."""

    model_config = ConfigDict(extra="forbid")

    code: str
    details: Any | None = None


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success envelope."""

    model_config = ConfigDict(extra="forbid")

    success: bool = True
    message: str
    data: T | None = None
    meta: ResponseMeta


class ErrorResponse(BaseModel):
    """Standard error envelope."""

    model_config = ConfigDict(extra="forbid")

    success: bool = False
    message: str
    error: ErrorDetail
    meta: ResponseMeta

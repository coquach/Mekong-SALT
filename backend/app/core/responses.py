"""Consistent API response helpers."""

from datetime import datetime, timezone
from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi import Request
from fastapi.responses import JSONResponse

from app.schemas.common import ErrorDetail, ErrorResponse, ResponseMeta, SuccessResponse


def _build_meta(request: Request | None) -> ResponseMeta:
    request_id = None
    if request is not None:
        request_id = getattr(request.state, "request_id", None)

    return ResponseMeta(
        request_id=request_id,
        timestamp=datetime.now(timezone.utc),
    )


def success_response(
    *,
    request: Request | None,
    message: str,
    data: Any = None,
    status_code: int = 200,
) -> JSONResponse:
    """Build a successful API response envelope."""
    payload = SuccessResponse[Any](
        message=message,
        data=data,
        meta=_build_meta(request),
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))


def error_response(
    *,
    request: Request | None,
    status_code: int,
    message: str,
    code: str,
    details: Any | None = None,
) -> JSONResponse:
    """Build a failed API response envelope."""
    # RequestValidationError may include raw Exception objects in context.
    safe_details = jsonable_encoder(
        details,
        custom_encoder={Exception: lambda exc: str(exc)},
    )

    payload = ErrorResponse(
        message=message,
        error=ErrorDetail(code=code, details=safe_details),
        meta=_build_meta(request),
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))


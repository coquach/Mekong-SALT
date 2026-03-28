"""Central exception types and FastAPI handlers."""

import logging
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.responses import error_response

logger = logging.getLogger(__name__)


class AppException(Exception):
    """Application-level exception with structured error metadata."""

    def __init__(
        self,
        *,
        status_code: int = HTTPStatus.BAD_REQUEST,
        code: str = "application_error",
        message: str = "Application error.",
        details: Any | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


def register_exception_handlers(application: FastAPI) -> None:
    """Register shared exception handlers on the application."""

    @application.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException):
        logger.warning("Application exception raised: %s", exc.code)
        return error_response(
            request=request,
            status_code=exc.status_code,
            message=exc.message,
            code=exc.code,
            details=exc.details,
        )

    @application.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ):
        return error_response(
            request=request,
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            message="Request validation failed.",
            code="validation_error",
            details=exc.errors(),
        )

    @application.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        request: Request, exc: StarletteHTTPException
    ):
        return error_response(
            request=request,
            status_code=exc.status_code,
            message=str(exc.detail),
            code="http_error",
        )

    @application.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception):
        logger.exception("Unhandled exception", exc_info=exc)
        return error_response(
            request=request,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            message="Internal server error.",
            code="internal_server_error",
        )

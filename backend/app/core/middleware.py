"""Shared middleware implementations."""

import logging
import time
from uuid import uuid4

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send


logger = logging.getLogger("app.request")


class RequestContextMiddleware:
    """Attach a request ID to each request/response pair."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = Headers(raw=scope["headers"]).get("x-request-id", str(uuid4()))
        state = scope.setdefault("state", {})
        state["request_id"] = request_id

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["X-Request-ID"] = request_id
            await send(message)

        await self.app(scope, receive, send_with_request_id)


class RequestLoggingMiddleware:
    """Emit structured logs for each HTTP request."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        started_at = time.perf_counter()
        status_code = 500

        async def send_with_status(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
            await send(message)

        try:
            await self.app(scope, receive, send_with_status)
        finally:
            duration_ms = (time.perf_counter() - started_at) * 1000
            state = scope.get("state") or {}
            client = scope.get("client")
            client_host = client[0] if isinstance(client, tuple) else None
            logger.info(
                "%s %s -> %s (%.2f ms)",
                scope.get("method", "UNKNOWN"),
                scope.get("path", ""),
                status_code,
                duration_ms,
                extra={
                    "request_id": state.get("request_id"),
                    "method": scope.get("method", "UNKNOWN"),
                    "path": scope.get("path", ""),
                    "status_code": status_code,
                    "duration_ms": round(duration_ms, 2),
                    "client": client_host,
                },
            )


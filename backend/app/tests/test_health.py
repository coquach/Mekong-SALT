"""Smoke tests for the bootstrap API."""

import pytest


@pytest.mark.anyio
async def test_health_endpoint_returns_standard_envelope(client):
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Service is healthy."
    assert body["data"]["service"] == "Mekong-SALT Backend"
    assert body["data"]["dependencies"]["database"] == "configured"
    assert "X-Request-ID" in response.headers


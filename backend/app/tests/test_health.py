"""Smoke tests for the bootstrap API."""

import pytest


@pytest.mark.asyncio
async def test_health_endpoint_returns_standard_envelope(client):
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Dịch vụ đang hoạt động bình thường."
    assert body["data"]["service"] == "Mekong-SALT Backend"
    assert body["data"]["dependencies"]["database"] == "configured"
    assert "X-Request-ID" in response.headers


@pytest.mark.asyncio
async def test_health_readiness_mode_returns_dependency_probe_status(client):
    response = await client.get("/api/v1/health", params={"mode": "readiness"})

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Trạng thái sẵn sàng đã được đánh giá."
    assert body["data"]["dependencies"]["database"] in {"ready", "unreachable"}
    assert body["data"]["dependencies"]["redis"] in {"ready", "unreachable"}


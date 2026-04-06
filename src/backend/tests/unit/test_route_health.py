"""Unit tests for the health check endpoint."""

import pytest


@pytest.mark.asyncio
async def test_health_returns_ok():
    from app.routers.health import health_check

    result = await health_check()
    assert result["status"] == "ok"


@pytest.mark.asyncio
async def test_health_returns_service_name():
    from app.routers.health import health_check

    result = await health_check()
    assert result["service"] == "hermes-backend"


@pytest.mark.asyncio
async def test_health_has_expected_keys():
    from app.routers.health import health_check

    result = await health_check()
    assert set(result.keys()) == {"status", "service"}

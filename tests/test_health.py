"""Tests for the health check endpoint.

Verifies:
- Health endpoint returns 200 when all components are healthy
- Health endpoint reports component status correctly
- No auth required for health endpoint
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


class TestHealth:
    """Health check endpoint tests."""

    async def test_health_returns_200(self, test_client: AsyncClient) -> None:
        """Health endpoint should return 200 OK."""
        response = await test_client.get("/health")
        assert response.status_code == 200

    async def test_health_has_expected_structure(
        self, test_client: AsyncClient
    ) -> None:
        """Response should include status and checks for all components."""
        response = await test_client.get("/health")
        data = response.json()

        assert "status" in data
        assert "checks" in data
        assert "db" in data["checks"]
        assert "vector_store" in data["checks"]
        assert "model" in data["checks"]
        assert "redis" in data["checks"]

    async def test_health_checks_have_status_field(
        self, test_client: AsyncClient
    ) -> None:
        """Each component check should have a status field."""
        response = await test_client.get("/health")
        data = response.json()

        for component, check in data["checks"].items():
            assert "status" in check, f"Missing status for {component}"
            assert check["status"] in ("up", "down"), (
                f"Invalid status for {component}: {check['status']}"
            )

    async def test_health_no_auth_required(
        self, test_client: AsyncClient
    ) -> None:
        """Health endpoint should work without any auth headers."""
        response = await test_client.get("/health", headers={})
        assert response.status_code == 200

    async def test_health_with_invalid_auth_should_still_work(
        self, test_client: AsyncClient
    ) -> None:
        """Health endpoint should work even with invalid auth headers."""
        response = await test_client.get(
            "/health", headers={"X-API-Key": "wrong-key"}
        )
        assert response.status_code == 200

    async def test_health_returns_json(self, test_client: AsyncClient) -> None:
        """Health endpoint should return JSON content type."""
        response = await test_client.get("/health")
        assert response.headers["content-type"].startswith("application/json")

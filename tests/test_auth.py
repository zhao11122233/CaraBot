"""Tests for API key authentication middleware.

Verifies:
- Missing X-API-Key header returns 400
- Invalid X-API-Key header returns 401
- Valid X-API-Key allows request through
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


class TestAuth:
    """Authentication middleware tests."""

    async def test_missing_api_key_returns_400(self, test_client: AsyncClient) -> None:
        """Request without X-API-Key header should return 400."""
        response = await test_client.post(
            "/api/v1/search",
            json={"query": "test query"},
            headers={},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "MISSING_API_KEY"

    async def test_empty_api_key_returns_400(self, test_client: AsyncClient) -> None:
        """Request with empty X-API-Key should return 400."""
        response = await test_client.post(
            "/api/v1/search",
            json={"query": "test query"},
            headers={"X-API-Key": ""},
        )
        assert response.status_code == 400

    async def test_invalid_api_key_returns_401(self, test_client: AsyncClient) -> None:
        """Request with wrong API key should return 401."""
        response = await test_client.post(
            "/api/v1/search",
            json={"query": "test query"},
            headers={"X-API-Key": "wrong-key"},
        )
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "INVALID_API_KEY"

    async def test_valid_api_key_passes_auth(
        self, test_client: AsyncClient, auth_headers: dict
    ) -> None:
        """Request with correct API key should pass authentication."""
        response = await test_client.post(
            "/api/v1/search",
            json={"query": "test query"},
            headers=auth_headers,
        )
        # Should NOT be 401 or 400 — search should execute (even if it returns empty results)
        assert response.status_code not in (401, 400, 403)

    async def test_health_endpoint_no_auth_required(
        self, test_client: AsyncClient
    ) -> None:
        """Health check endpoint should work without authentication."""
        response = await test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data

    async def test_stats_requires_auth(self, test_client: AsyncClient) -> None:
        """Stats endpoint should require authentication."""
        response = await test_client.get("/api/v1/stats")
        assert response.status_code in (400, 401)

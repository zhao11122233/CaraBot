"""Tests for the search endpoint.

Verifies:
- Search returns results in correct format
- Empty query returns validation error
- Search respects top_k and threshold parameters
- Auth is required
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


class TestSearch:
    """Search endpoint tests."""

    async def test_search_requires_auth(self, test_client: AsyncClient) -> None:
        """Search without auth should be rejected."""
        response = await test_client.post(
            "/api/v1/search",
            json={"query": "test"},
            headers={},
        )
        assert response.status_code in (400, 401)

    async def test_search_with_valid_auth(
        self, test_client: AsyncClient, auth_headers: dict
    ) -> None:
        """Search with valid auth should return results."""
        response = await test_client.post(
            "/api/v1/search",
            json={"query": "How to reset password?"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "total_results" in data
        assert "results" in data
        assert "search_time_ms" in data
        assert isinstance(data["results"], list)

    async def test_search_empty_query_returns_error(
        self, test_client: AsyncClient, auth_headers: dict
    ) -> None:
        """Empty query string should return validation error."""
        response = await test_client.post(
            "/api/v1/search",
            json={"query": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422  # Pydantic validation error

    async def test_search_with_custom_top_k(
        self, test_client: AsyncClient, auth_headers: dict
    ) -> None:
        """Custom top_k should be accepted."""
        response = await test_client.post(
            "/api/v1/search",
            json={"query": "test", "top_k": 10},
            headers=auth_headers,
        )
        assert response.status_code == 200

    async def test_search_with_threshold(
        self, test_client: AsyncClient, auth_headers: dict
    ) -> None:
        """Custom threshold should be accepted."""
        response = await test_client.post(
            "/api/v1/search",
            json={"query": "test", "threshold": 0.8},
            headers=auth_headers,
        )
        assert response.status_code == 200

    async def test_search_with_collection(
        self, test_client: AsyncClient, auth_headers: dict
    ) -> None:
        """Custom collection parameter should be accepted."""
        response = await test_client.post(
            "/api/v1/search",
            json={"query": "test", "collection": "faq"},
            headers=auth_headers,
        )
        assert response.status_code == 200

    async def test_search_invalid_threshold_rejected(
        self, test_client: AsyncClient, auth_headers: dict
    ) -> None:
        """Threshold > 1.0 should be rejected."""
        response = await test_client.post(
            "/api/v1/search",
            json={"query": "test", "threshold": 1.5},
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_search_response_structure(
        self, test_client: AsyncClient, auth_headers: dict
    ) -> None:
        """Each result should have document_id, content, score, and metadata."""
        response = await test_client.post(
            "/api/v1/search",
            json={"query": "test query"},
            headers=auth_headers,
        )
        data = response.json()
        for result in data["results"]:
            assert "document_id" in result
            assert "content" in result
            assert "score" in result
            assert "metadata" in result
            assert 0.0 <= result["score"] <= 1.0

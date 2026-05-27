"""GET /api/v1/stats — Statistics endpoint."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from src.app.middleware.auth import AuthGuard
from src.app.services.stats_service import StatsService

logger = logging.getLogger(__name__)


def create_stats_router(auth_guard: AuthGuard, stats_service: StatsService) -> APIRouter:
    """Factory for the stats router with injected dependencies.

    Args:
        auth_guard: API key authentication dependency.
        stats_service: Statistics service.

    Returns:
        Configured APIRouter instance.
    """
    router = APIRouter(tags=["Stats"])

    @router.get("/stats")
    async def get_stats(
        _api_key: str = Depends(auth_guard),
    ) -> dict:
        """Get knowledge base statistics.

        Returns total documents, total chunks, per-collection breakdown,
        active vector store type, and last update timestamp.
        """
        return await stats_service.get_stats()

    return router

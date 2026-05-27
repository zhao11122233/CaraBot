"""POST /api/v1/search — Semantic search endpoint."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from src.app.middleware.auth import AuthGuard
from src.app.models.schemas import SearchRequest
from src.app.services.search_service import SearchService

logger = logging.getLogger(__name__)


def create_search_router(auth_guard: AuthGuard, search_service: SearchService) -> APIRouter:
    """Factory for the search router with injected dependencies.

    Args:
        auth_guard: API key authentication dependency.
        search_service: Search orchestration service.

    Returns:
        Configured APIRouter instance.
    """
    router = APIRouter(tags=["Search"])

    @router.post("/search")
    async def search(
        body: SearchRequest,
        _api_key: str = Depends(auth_guard),
    ) -> dict:
        """Search the knowledge base with a text query.

        Returns top-K most relevant document chunks with similarity scores.
        Results are filtered by the similarity threshold.
        """
        result = await search_service.search(
            query=body.query,
            top_k=body.top_k,
            threshold=body.threshold,
            collection=body.collection,
        )
        return result

    return router

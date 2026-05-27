"""GET /health — Health check endpoint (no auth required).

Checks all dependency components: database, vector store, embedding model, Redis.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.app.services.embedding_service import EmbeddingService
from src.app.vectorstore.base import BaseVectorStore

logger = logging.getLogger(__name__)


def create_health_router(
    session_factory: async_sessionmaker[AsyncSession],
    vector_store: BaseVectorStore,
    embedding_service: EmbeddingService,
    redis_url: str,
) -> APIRouter:
    """Factory for the health check router (no auth required).

    Args:
        session_factory: Async SQLAlchemy session factory for DB health check.
        vector_store: Vector store for connection check.
        embedding_service: Embedding service for model check.
        redis_url: Redis connection URL for Redis health check.

    Returns:
        Configured APIRouter instance.
    """
    router = APIRouter(tags=["Health"])

    @router.get("/health")
    async def health_check() -> dict:
        """Check the health of all dependency components.

        Returns per-component status (up/down) with details on failure.
        The overall 'status' is 'up' only if ALL components are healthy.
        """
        checks = {}

        # Database check
        try:
            async with session_factory() as session:
                await session.execute(text("SELECT 1"))
            checks["db"] = {"status": "up", "detail": None}
        except Exception as exc:
            logger.error("DB health check failed: %s", exc)
            checks["db"] = {"status": "down", "detail": str(exc)}

        # Vector store check
        try:
            vs_healthy = await vector_store.health_check()
            checks["vector_store"] = {
                "status": "up" if vs_healthy else "down",
                "detail": None if vs_healthy else "Vector store not reachable",
            }
        except Exception as exc:
            logger.error("Vector store health check failed: %s", exc)
            checks["vector_store"] = {"status": "down", "detail": str(exc)}

        # Model check
        try:
            model_healthy = await embedding_service.health_check()
            checks["model"] = {
                "status": "up" if model_healthy else "down",
                "detail": None if model_healthy else "Model not loaded or inference failed",
            }
        except Exception as exc:
            logger.error("Model health check failed: %s", exc)
            checks["model"] = {"status": "down", "detail": str(exc)}

        # Redis check
        try:
            import redis.asyncio as aioredis
            r = aioredis.from_url(redis_url)
            await r.ping()
            await r.aclose()
            checks["redis"] = {"status": "up", "detail": None}
        except Exception as exc:
            logger.error("Redis health check failed: %s", exc)
            checks["redis"] = {"status": "down", "detail": str(exc)}

        overall = "up" if all(c["status"] == "up" for c in checks.values()) else "down"

        return {"status": overall, "checks": checks}

    return router

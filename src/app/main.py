"""CaraBot FastAPI application factory.

Creates the FastAPI app with all middleware, services, and routes wired together.
Uses the lifespan pattern for graceful startup validation and shutdown.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.app.api import register_routers
from src.app.core.config import load_settings
from src.app.core.logging import setup_logging
from src.app.middleware.auth import AuthGuard
from src.app.middleware.error_handler import register_error_handlers
from src.app.middleware.logging import RequestLoggingMiddleware
from src.app.models import create_engine_and_session
from src.app.services.dedup_service import DedupService
from src.app.services.document_processor import DocumentProcessor
from src.app.services.embedding_service import EmbeddingService
from src.app.services.search_service import SearchService
from src.app.services.stats_service import StatsService
from src.app.services.upload_service import UploadService
from src.app.vectorstore import get_vector_store

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the CaraBot FastAPI application.

    Returns:
        Fully configured FastAPI application ready to serve.
    """
    # Load and validate configuration (exits on failure)
    settings = load_settings()

    # Setup JSON logging before anything else
    setup_logging(settings)

    logger.info(
        "Starting CaraBot (vector_store=%s, log_level=%s)",
        settings.vector_store_type,
        settings.log_level,
    )

    # Initialize database
    db_engine, session_factory = create_engine_and_session(settings)

    # Initialize vector store
    vector_store = get_vector_store(settings)

    # Initialize embedding service
    embedding_service = EmbeddingService(settings)

    # Initialize services
    doc_processor = DocumentProcessor(settings)
    dedup_service = DedupService(session_factory)
    upload_service = UploadService(
        settings, doc_processor, embedding_service, vector_store, dedup_service
    )
    search_service = SearchService(settings, embedding_service, vector_store)
    stats_service = StatsService(settings, dedup_service, vector_store)

    # Initialize auth guard
    auth_guard = AuthGuard(settings)

    # --- Lifespan: startup validation ---
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Startup: validate all dependencies. Shutdown: close connections."""
        logger.info("Running startup checks...")
        errors = []

        # Check database
        try:
            from sqlalchemy import text
            async with session_factory() as session:
                await session.execute(text("SELECT 1"))
            logger.info("  [OK] Database connection verified")
        except Exception as exc:
            errors.append(f"Database: {exc}")
            logger.error("  [FAIL] Database: %s", exc)

        # Create tables if not exist
        try:
            from src.app.models import Base
            async with db_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("  [OK] Database tables ensured")
        except Exception as exc:
            errors.append(f"Database migration: {exc}")
            logger.error("  [FAIL] Database migration: %s", exc)

        # Check vector store
        try:
            vs_ok = await vector_store.health_check()
            if vs_ok:
                logger.info("  [OK] Vector store (%s) connected", settings.vector_store_type)
            else:
                errors.append("Vector store: unreachable")
                logger.error("  [FAIL] Vector store (%s) unreachable", settings.vector_store_type)
        except Exception as exc:
            errors.append(f"Vector store: {exc}")
            logger.error("  [FAIL] Vector store: %s", exc)

        # Load embedding model
        try:
            await embedding_service.startup()
            logger.info("  [OK] Embedding model loaded")
        except Exception as exc:
            errors.append(f"Embedding model: {exc}")
            logger.error("  [FAIL] Embedding model: %s", exc)

        # Check Redis
        try:
            import redis.asyncio as aioredis
            r = aioredis.from_url(settings.redis_url)
            await r.ping()
            await r.aclose()
            logger.info("  [OK] Redis connected")
        except Exception as exc:
            logger.warning("  [WARN] Redis not available: %s", exc)
            # Redis is optional for P1 — don't block startup

        if errors:
            logger.critical("Startup validation failed: %s", "; ".join(errors))
            # Don't exit; let health endpoint report status

        logger.info("CaraBot ready on %s:%s", settings.host, settings.port)
        yield

        # Shutdown
        logger.info("Shutting down CaraBot...")
        await db_engine.dispose()
        logger.info("CaraBot shutdown complete.")

    # --- Create the application ---
    app = FastAPI(
        title="CaraBot",
        description="Enterprise multi-language RAG knowledge retrieval module",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Register middleware (order matters: logging → error → auth)
    app.add_middleware(RequestLoggingMiddleware)
    register_error_handlers(app)

    # Register API routes
    register_routers(
        app,
        auth_guard,
        upload_service,
        search_service,
        stats_service,
        session_factory,
        vector_store,
        embedding_service,
        settings.redis_url,
    )

    return app

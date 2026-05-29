"""API route aggregation and registration."""

from fastapi import APIRouter, FastAPI

from src.app.api.routes.chat import create_chat_router
from src.app.api.routes.health import create_health_router
from src.app.api.routes.search import create_search_router
from src.app.api.routes.stats import create_stats_router
from src.app.api.routes.upload import create_upload_router


def register_routers(
    app: FastAPI,
    auth_guard,
    upload_service,
    search_service,
    stats_service,
    session_factory,
    vector_store,
    embedding_service,
    redis_url: str,
    agent_service=None,
) -> None:
    """Create and register all API routers on the FastAPI application.

    /health is public (no auth); /api/v1/* routes require authentication.
    """
    # Public health endpoint (no auth)
    health_router = create_health_router(
        session_factory, vector_store, embedding_service, redis_url
    )
    app.include_router(health_router)

    # Protected API routes
    api_router = APIRouter(prefix="/api/v1")

    upload_router = create_upload_router(auth_guard, upload_service)
    api_router.include_router(upload_router)

    search_router = create_search_router(auth_guard, search_service)
    api_router.include_router(search_router)

    stats_router = create_stats_router(auth_guard, stats_service)
    api_router.include_router(stats_router)

    if agent_service is not None:
        chat_router = create_chat_router(auth_guard, agent_service)
        api_router.include_router(chat_router)

    app.include_router(api_router)

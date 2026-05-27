"""Unified error handling for FastAPI.

Registers exception handlers that convert all CaraBotException subclasses
into consistent JSON error responses with trace_id.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.app.core.exceptions import CaraBotException
from src.app.core.logging import get_trace_id

logger = logging.getLogger(__name__)


def register_error_handlers(app: FastAPI) -> None:
    """Register exception handlers on the FastAPI application.

    Args:
        app: The FastAPI app instance.
    """

    @app.exception_handler(CaraBotException)
    async def carabot_exception_handler(
        request: Request, exc: CaraBotException
    ) -> JSONResponse:
        """Handle all CaraBot exceptions with consistent error format."""
        trace_id = get_trace_id()
        logger.error(
            "Error [%s]: %s (status=%d, trace_id=%s)",
            exc.code, exc.message, exc.status_code, trace_id,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "trace_id": trace_id,
                    "detail": exc.detail if exc.detail else None,
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Catch-all for unexpected exceptions. Logs stack trace and returns 500."""
        trace_id = get_trace_id()
        logger.exception(
            "Unhandled exception (trace_id=%s): %s", trace_id, exc
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected internal error occurred.",
                    "trace_id": trace_id,
                }
            },
        )

    @app.exception_handler(405)
    async def method_not_allowed_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle 405 Method Not Allowed."""
        trace_id = get_trace_id()
        return JSONResponse(
            status_code=405,
            content={
                "error": {
                    "code": "METHOD_NOT_ALLOWED",
                    "message": f"Method {request.method} not allowed for {request.url.path}.",
                    "trace_id": trace_id,
                }
            },
        )

    @app.exception_handler(404)
    async def not_found_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle 404 Not Found."""
        trace_id = get_trace_id()
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Path '{request.url.path}' not found.",
                    "trace_id": trace_id,
                }
            },
        )

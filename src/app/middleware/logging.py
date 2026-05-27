"""ASGI request logging middleware.

Generates a trace_id for every request and logs request/response metadata
in JSON format. trace_id is stored in a contextvar for access throughout
the request lifecycle.
"""

from __future__ import annotations

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from src.app.core.logging import set_trace_id

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs every HTTP request with trace_id, method, path, status, and duration."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Generate trace_id, log the request, and attach trace_id to the response."""
        # Generate and set trace_id for this request
        trace_id = set_trace_id()

        start_time = time.perf_counter()

        # Attach trace_id to request state for downstream access
        request.state.trace_id = trace_id

        # Process the request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Attach trace_id to response headers for client-side tracing
        response.headers["X-Trace-ID"] = trace_id

        # Log request summary
        logger.info(
            "%s %s → %d (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        return response

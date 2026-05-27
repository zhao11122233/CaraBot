"""API Key authentication middleware.

Validates the X-API-Key header on every protected request.
Missing header → 400, invalid key → 401.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import Header

from src.app.core.config import Settings
from src.app.core.exceptions import InvalidApiKeyException, MissingApiKeyException

logger = logging.getLogger(__name__)


class AuthGuard:
    """FastAPI dependency that validates the X-API-Key header."""

    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.api_key

    async def __call__(
        self, x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None
    ) -> str:
        """Validate the API key from the request header.

        Args:
            x_api_key: Value of the X-API-Key header.

        Returns:
            The validated API key string.

        Raises:
            MissingApiKeyException: Header is absent or empty (400).
            InvalidApiKeyException: Header value does not match (401).
        """
        if not x_api_key:
            logger.warning("Request rejected: missing X-API-Key header")
            raise MissingApiKeyException()

        if x_api_key != self._api_key:
            logger.warning("Request rejected: invalid API key")
            raise InvalidApiKeyException()

        return x_api_key

"""Unified exception hierarchy for CaraBot.

All application exceptions inherit from CaraBotException, enabling consistent
error formatting and HTTP status mapping in the error handler middleware.
"""

from __future__ import annotations


class CaraBotException(Exception):
    """Base exception for all CaraBot errors."""

    code: str = "INTERNAL_ERROR"
    status_code: int = 500
    message: str = "An internal error occurred."

    def __init__(self, message: str | None = None, detail: dict | None = None) -> None:
        self.message = message or self.message
        self.detail = detail or {}
        super().__init__(self.message)


class AuthException(CaraBotException):
    """Authentication or authorization failure."""

    code = "AUTH_ERROR"
    status_code = 401
    message = "Authentication failed."


class MissingApiKeyException(AuthException):
    """API key is missing from the request."""

    code = "MISSING_API_KEY"
    status_code = 400
    message = "X-API-Key header is required."


class InvalidApiKeyException(AuthException):
    """API key is present but invalid."""

    code = "INVALID_API_KEY"
    status_code = 401
    message = "Invalid API key."


class DocumentException(CaraBotException):
    """Document processing error (unsupported format, unreadable file, etc.)."""

    code = "DOCUMENT_ERROR"
    status_code = 422
    message = "Document processing failed."


class UnsupportedFileTypeException(DocumentException):
    """Uploaded file has an unsupported MIME type."""

    code = "UNSUPPORTED_FILE_TYPE"
    status_code = 415
    message = "Unsupported file type. Supported formats: PDF, DOCX, MD, TXT."


class FileTooLargeException(DocumentException):
    """Uploaded file exceeds the maximum allowed size."""

    code = "FILE_TOO_LARGE"
    status_code = 413
    message = "File size exceeds the maximum allowed."


class EmbeddingException(CaraBotException):
    """Embedding model error (model not loaded, inference failure, etc.)."""

    code = "EMBEDDING_ERROR"
    status_code = 500
    message = "Embedding model error."


class VectorStoreException(CaraBotException):
    """Vector store connection or operation error."""

    code = "VECTOR_STORE_ERROR"
    status_code = 500
    message = "Vector store error."


class ConfigurationException(CaraBotException):
    """Invalid or missing configuration at startup."""

    code = "CONFIG_ERROR"
    status_code = 500
    message = "Configuration error."


class HealthCheckException(CaraBotException):
    """A dependency health check failed."""

    code = "SERVICE_UNAVAILABLE"
    status_code = 503
    message = "One or more dependencies are unavailable."

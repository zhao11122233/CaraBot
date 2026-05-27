"""POST /api/v1/upload — Document upload endpoint."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile

from src.app.middleware.auth import AuthGuard
from src.app.services.upload_service import UploadService

logger = logging.getLogger(__name__)


def create_upload_router(auth_guard: AuthGuard, upload_service: UploadService) -> APIRouter:
    """Factory for the upload router with injected dependencies.

    Args:
        auth_guard: API key authentication dependency.
        upload_service: Upload orchestration service.

    Returns:
        Configured APIRouter instance.
    """
    router = APIRouter(tags=["Upload"])

    @router.post("/upload")
    async def upload_document(
        file: Annotated[UploadFile, File(description="Document to upload and index")],
        author: Annotated[str | None, Form(description="Document author")] = None,
        collection: Annotated[str | None, Form(description="Target collection name")] = None,
        _api_key: str = Depends(auth_guard),
    ) -> dict:
        """Upload and index a document for RAG search.

        Supported formats: PDF, DOCX, Markdown, TXT.
        Duplicate files (by SHA256 hash) return the existing document_id.
        Files with the same name but different content trigger incremental update.
        """
        content = await file.read()

        if not content:
            from src.app.core.exceptions import DocumentException
            raise DocumentException("Uploaded file is empty.")

        mime_type = file.content_type or None

        result = await upload_service.upload(
            file_content=content,
            filename=file.filename or "unnamed",
            mime_type=mime_type,
            author=author,
            collection=collection,
        )

        return result

    return router

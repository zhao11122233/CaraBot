"""Upload orchestration service.

Coordinates the full pipeline: hash → dedup → parse → chunk → embed → store → register.
"""

from __future__ import annotations

import logging
import uuid

from langchain_core.documents import Document

from src.app.core.config import Settings
from src.app.core.exceptions import DocumentException, FileTooLargeException
from src.app.services.dedup_service import DedupService
from src.app.services.document_processor import DocumentProcessor
from src.app.services.embedding_service import EmbeddingService
from src.app.vectorstore.base import BaseVectorStore

logger = logging.getLogger(__name__)


class UploadService:
    """Orchestrates document upload, dedup, parsing, embedding, and storage."""

    def __init__(
        self,
        settings: Settings,
        doc_processor: DocumentProcessor,
        embedding_service: EmbeddingService,
        vector_store: BaseVectorStore,
        dedup_service: DedupService,
    ) -> None:
        self._settings = settings
        self._doc_processor = doc_processor
        self._embedding_service = embedding_service
        self._vector_store = vector_store
        self._dedup_service = dedup_service

    async def upload(
        self,
        file_content: bytes,
        filename: str,
        mime_type: str | None = None,
        author: str | None = None,
        collection: str | None = None,
    ) -> dict:
        """Process and index a single uploaded document.

        Args:
            file_content: Raw file bytes.
            filename: Original filename.
            mime_type: MIME type (auto-detected if None).
            author: Optional document author.
            collection: Target vector store collection (uses default if None).

        Returns:
            Dict with document_id, filename, file_hash, file_size, chunk_count, is_duplicate.
        """
        # Validate file size
        file_size = len(file_content)
        if file_size > self._settings.max_file_size:
            raise FileTooLargeException(
                f"File '{filename}' is {file_size} bytes (max {self._settings.max_file_size})."
            )

        # Compute hash and check for duplicates
        file_hash = self._dedup_service.compute_hash(file_content)
        existing = await self._dedup_service.check_duplicate(file_hash)

        if existing is not None:
            logger.info("Duplicate file, returning existing record: %s", existing.id)
            return {
                "document_id": str(existing.id),
                "filename": existing.filename,
                "file_hash": existing.file_hash,
                "file_size": existing.file_size,
                "chunk_count": existing.chunk_count,
                "is_duplicate": True,
                "message": "File already indexed.",
            }

        # Check for incremental update (same filename, different hash)
        col_name = collection or self._settings.milvus_collection_name
        old_record = await self._dedup_service.find_by_filename(filename)
        old_doc_id = None
        if old_record is not None:
            logger.info(
                "Incremental update for '%s': old_hash=%s, new_hash=%s",
                filename, old_record.file_hash[:16], file_hash[:16],
            )
            old_doc_id = str(old_record.id)
            await self._vector_store.delete([old_doc_id], col_name)
            await self._dedup_service.mark_deleted(old_doc_id)

        # Parse and chunk
        chunks = await self._doc_processor.load_and_split(file_content, filename, mime_type)

        # Generate document ID
        doc_id = str(uuid.uuid4())

        # Embed chunks
        texts = [chunk.page_content for chunk in chunks]
        embeddings = await self._embedding_service.embed_documents(texts)

        # Prepare documents with metadata
        for chunk in chunks:
            chunk.metadata["document_id"] = doc_id
            chunk.metadata["filename"] = filename
            chunk.metadata["author"] = author or ""
            chunk.metadata["file_hash"] = file_hash

        # Store in vector DB with BGE-m3 embeddings
        chunk_ids = await self._vector_store.add_documents(chunks, col_name, embeddings)

        # Register in PostgreSQL with the same doc_id used in chunk metadata
        mime = mime_type or "application/octet-stream"
        await self._dedup_service.register_document(
            filename=filename,
            file_hash=file_hash,
            file_size=file_size,
            mime_type=mime,
            chunk_count=len(chunks),
            collection_name=col_name,
            author=author,
            doc_id=doc_id,
        )

        logger.info(
            "Upload complete: doc_id=%s, file='%s', chunks=%d, incremental=%s",
            doc_id, filename, len(chunks), old_doc_id is not None,
        )

        return {
            "document_id": doc_id,
            "filename": filename,
            "file_hash": file_hash,
            "file_size": file_size,
            "chunk_count": len(chunks),
            "is_duplicate": False,
            "message": (
                "Document updated successfully (incremental update)."
                if old_doc_id
                else "Document processed successfully."
            ),
        }

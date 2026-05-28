"""Document deduplication via SHA256 hashing with PostgreSQL.

Handles duplicate detection and incremental updates: same hash returns existing
document_id; same filename with different hash triggers old-vector deletion.
"""

from __future__ import annotations

import hashlib
import logging
import uuid as _uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.app.core.exceptions import DocumentException
from src.app.models.document import DocumentRecord

logger = logging.getLogger(__name__)


class DedupService:
    """Manages document deduplication and incremental update logic."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    @staticmethod
    def compute_hash(content: bytes) -> str:
        """Compute SHA256 hash of file content."""
        return hashlib.sha256(content).hexdigest()

    async def check_duplicate(self, file_hash: str) -> DocumentRecord | None:
        """Check if a file with this hash has already been indexed.

        Args:
            file_hash: SHA256 hash of file content.

        Returns:
            Existing DocumentRecord if found, None otherwise.
        """
        async with self._session_factory() as session:
            result = await session.execute(
                select(DocumentRecord)
                .where(DocumentRecord.file_hash == file_hash)
                .where(DocumentRecord.status == "active")
                .limit(1)
            )
            record = result.scalar_one_or_none()
            if record:
                logger.info("Duplicate detected: hash=%s, doc_id=%s", file_hash[:16], record.id)
            return record

    async def find_by_filename(self, filename: str) -> DocumentRecord | None:
        """Find the latest active record for a given filename."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(DocumentRecord)
                .where(DocumentRecord.filename == filename)
                .where(DocumentRecord.status == "active")
                .order_by(DocumentRecord.created_at.desc())
                .limit(1)
            )
            return result.scalar_one_or_none()

    async def register_document(
        self,
        filename: str,
        file_hash: str,
        file_size: int,
        mime_type: str,
        chunk_count: int,
        collection_name: str,
        author: str | None = None,
        doc_id: str | None = None,
    ) -> DocumentRecord:
        """Insert a new document record into PostgreSQL.

        Args:
            filename: Original filename.
            file_hash: SHA256 hash.
            file_size: File size in bytes.
            mime_type: MIME type.
            chunk_count: Number of chunks created.
            collection_name: Vector store collection.
            author: Optional document author.
            doc_id: Optional pre-generated document ID (for consistent vector store linkage).

        Returns:
            The newly created DocumentRecord.
        """
        async with self._session_factory() as session:
            kwargs: dict = {
                "filename": filename,
                "file_hash": file_hash,
                "file_size": file_size,
                "author": author,
                "mime_type": mime_type,
                "chunk_count": chunk_count,
                "collection_name": collection_name,
                "status": "active",
            }
            if doc_id is not None:
                kwargs["id"] = _uuid.UUID(doc_id)
            record = DocumentRecord(**kwargs)
            session.add(record)
            await session.commit()
            await session.refresh(record)
            logger.info("Registered document: id=%s, filename='%s'", record.id, filename)
            return record

    @staticmethod
    def _to_uuid(doc_id: str) -> _uuid.UUID:
        """Convert a string to UUID, handling cross-DB compatibility."""
        return _uuid.UUID(doc_id) if isinstance(doc_id, str) else doc_id

    async def mark_deleted(self, doc_id: str) -> None:
        """Soft-delete a document record by setting status='deleted'."""
        uid = self._to_uuid(doc_id)
        async with self._session_factory() as session:
            await session.execute(
                update(DocumentRecord)
                .where(DocumentRecord.id == uid)
                .values(status="deleted", updated_at=datetime.now(timezone.utc))
            )
            await session.commit()
            logger.info("Marked document %s as deleted", doc_id)

    async def get_document(self, doc_id: str) -> DocumentRecord | None:
        """Retrieve a document record by ID."""
        uid = self._to_uuid(doc_id)
        async with self._session_factory() as session:
            result = await session.execute(
                select(DocumentRecord).where(DocumentRecord.id == uid)
            )
            return result.scalar_one_or_none()

    async def get_total_documents(self) -> int:
        """Count total active documents."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(DocumentRecord).where(DocumentRecord.status == "active")
            )
            return len(result.scalars().all())

    async def get_total_chunks(self) -> int:
        """Sum chunk_count across all active documents."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(DocumentRecord).where(DocumentRecord.status == "active")
            )
            records = result.scalars().all()
            return sum(r.chunk_count for r in records)

    async def get_latest_timestamp(self) -> datetime | None:
        """Get the most recent created_at from active documents."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(DocumentRecord.created_at)
                .where(DocumentRecord.status == "active")
                .order_by(DocumentRecord.created_at.desc())
                .limit(1)
            )
            ts = result.scalar_one_or_none()
            return ts

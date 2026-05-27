"""Document metadata ORM model for PostgreSQL.

Stores document metadata, SHA256 hashes, and indexing status. The hash column
enables deduplication; the status column supports soft-delete for incremental updates.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.app.models import Base


class DocumentRecord(Base):
    """Stores metadata for each uploaded and indexed document."""

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False, comment="Original file name")
    file_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True, comment="SHA256 hash of file content"
    )
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, comment="File size in bytes")
    author: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="Document author if available")
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False, comment="MIME type")
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, comment="Number of text chunks")
    collection_name: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="Vector store collection name"
    )
    status: Mapped[str] = mapped_column(
        String(16), default="active", comment="active | deleted"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="Record creation time"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last update time",
    )

    __table_args__ = (
        Index("idx_documents_status", "status"),
        Index("idx_documents_filename_hash", "filename", "file_hash"),
    )

    def __repr__(self) -> str:
        return f"<DocumentRecord(id={self.id}, filename='{self.filename}', status='{self.status}')>"

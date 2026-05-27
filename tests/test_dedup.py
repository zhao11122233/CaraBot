"""Tests for document deduplication service.

Verifies:
- SHA256 hash computation is deterministic
- Duplicate detection returns existing record
- Incremental update handles same-name/different-hash
"""

from __future__ import annotations

import uuid

import pytest

from src.app.models.document import DocumentRecord
from src.app.services.dedup_service import DedupService


pytestmark = pytest.mark.asyncio


class TestDedupService:
    """Deduplication logic tests."""

    @pytest.fixture
    async def dedup(self, db_engine_and_session) -> DedupService:
        """Create DedupService with test database."""
        _, session_factory = db_engine_and_session
        return DedupService(session_factory)

    async def test_compute_hash_deterministic(self, dedup: DedupService) -> None:
        """SHA256 hash of the same content should always be identical."""
        content = b"hello world"
        h1 = dedup.compute_hash(content)
        h2 = dedup.compute_hash(content)
        assert h1 == h2
        assert len(h1) == 64  # SHA256 hex digest is 64 chars

    async def test_compute_hash_different_for_different_content(self, dedup: DedupService) -> None:
        """Different content should produce different hashes."""
        h1 = dedup.compute_hash(b"hello")
        h2 = dedup.compute_hash(b"world")
        assert h1 != h2

    async def test_check_duplicate_returns_none_for_new_hash(
        self, dedup: DedupService
    ) -> None:
        """Unknown hash should return None."""
        result = await dedup.check_duplicate("a" * 64)
        assert result is None

    async def test_check_duplicate_returns_record_for_existing_hash(
        self, dedup: DedupService
    ) -> None:
        """Known hash should return the existing document record."""
        file_hash = "b" * 64
        record = await dedup.register_document(
            filename="test.pdf",
            file_hash=file_hash,
            file_size=1024,
            mime_type="application/pdf",
            chunk_count=5,
            collection_name="default",
        )
        result = await dedup.check_duplicate(file_hash)
        assert result is not None
        assert str(result.id) == str(record.id)
        assert result.file_hash == file_hash

    async def test_register_document_creates_record(
        self, dedup: DedupService
    ) -> None:
        """Registering a document should persist it in the database."""
        record = await dedup.register_document(
            filename="guide.pdf",
            file_hash="c" * 64,
            file_size=2048,
            mime_type="application/pdf",
            chunk_count=10,
            collection_name="default",
            author="John Doe",
        )
        assert record.id is not None
        assert record.filename == "guide.pdf"
        assert record.author == "John Doe"
        assert record.status == "active"

    async def test_mark_deleted_soft_deletes(self, dedup: DedupService) -> None:
        """Marking deleted should set status to 'deleted'."""
        record = await dedup.register_document(
            filename="old.pdf",
            file_hash="d" * 64,
            file_size=512,
            mime_type="application/pdf",
            chunk_count=2,
            collection_name="default",
        )
        await dedup.mark_deleted(str(record.id))

        # Should not appear in active queries
        result = await dedup.check_duplicate("d" * 64)
        assert result is None

    async def test_incremental_update_different_hash_same_filename(
        self, dedup: DedupService
    ) -> None:
        """Same filename, different hash should allow new record after old deleted."""
        filename = "report.pdf"

        # Register first version
        r1 = await dedup.register_document(
            filename=filename,
            file_hash="e" * 64,
            file_size=1024,
            mime_type="application/pdf",
            chunk_count=3,
            collection_name="default",
        )
        # Mark old as deleted (simulating incremental update)
        await dedup.mark_deleted(str(r1.id))

        # Register second version
        r2 = await dedup.register_document(
            filename=filename,
            file_hash="f" * 64,
            file_size=2048,
            mime_type="application/pdf",
            chunk_count=6,
            collection_name="default",
        )
        assert str(r2.id) != str(r1.id)

    async def test_get_total_documents(self, dedup: DedupService) -> None:
        """Total count should reflect active documents."""
        count_before = await dedup.get_total_documents()
        await dedup.register_document(
            filename="a.pdf", file_hash="g" * 64, file_size=100,
            mime_type="application/pdf", chunk_count=1, collection_name="default",
        )
        await dedup.register_document(
            filename="b.pdf", file_hash="h" * 64, file_size=200,
            mime_type="application/pdf", chunk_count=2, collection_name="default",
        )
        total = await dedup.get_total_documents()
        assert total == count_before + 2

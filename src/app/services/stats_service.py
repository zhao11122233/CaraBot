"""Statistics aggregation service.

Collects metrics from PostgreSQL and the vector store for the /stats endpoint.
"""

from __future__ import annotations

import logging

from src.app.core.config import Settings
from src.app.services.dedup_service import DedupService
from src.app.vectorstore.base import BaseVectorStore

logger = logging.getLogger(__name__)


class StatsService:
    """Aggregates statistics across PostgreSQL and the vector store."""

    def __init__(
        self,
        settings: Settings,
        dedup_service: DedupService,
        vector_store: BaseVectorStore,
    ) -> None:
        self._settings = settings
        self._dedup_service = dedup_service
        self._vector_store = vector_store

    async def get_stats(self) -> dict:
        """Collect and return aggregated statistics.

        Returns:
            Dict ready for JSON serialization as StatsResponse.
        """
        total_docs = await self._dedup_service.get_total_documents()
        total_chunks = await self._dedup_service.get_total_chunks()
        last_updated = await self._dedup_service.get_latest_timestamp()

        # Get vector store stats for default collection
        store_stats = await self._vector_store.get_collection_stats(None)

        collections = [
            {
                "collection_name": store_stats.get("name", "default"),
                "document_count": total_docs,
                "chunk_count": store_stats.get("count", 0),
            }
        ]

        return {
            "total_documents": total_docs,
            "total_chunks": total_chunks,
            "collections": collections,
            "vector_store_type": self._settings.vector_store_type,
            "last_updated": last_updated.isoformat() if last_updated else None,
        }

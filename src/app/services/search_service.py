"""Search orchestration service.

Embeds the query, searches the vector store, and formats results.
"""

from __future__ import annotations

import logging
import time

from src.app.core.config import Settings
from src.app.services.embedding_service import EmbeddingService
from src.app.vectorstore.base import BaseVectorStore

logger = logging.getLogger(__name__)


class SearchService:
    """Orchestrates semantic search: embed query → vector search → format results."""

    def __init__(
        self,
        settings: Settings,
        embedding_service: EmbeddingService,
        vector_store: BaseVectorStore,
    ) -> None:
        self._settings = settings
        self._embedding_service = embedding_service
        self._vector_store = vector_store

    async def search(
        self,
        query: str,
        top_k: int | None = None,
        threshold: float | None = None,
        collection: str | None = None,
    ) -> dict:
        """Execute a semantic search.

        Args:
            query: Search query text.
            top_k: Number of results (default from config).
            threshold: Minimum similarity score (default from config).
            collection: Vector store collection (uses default if None).

        Returns:
            Dict with query, total_results, results list, and search_time_ms.
        """
        top_k = top_k or self._settings.top_k
        threshold = threshold if threshold is not None else self._settings.similarity_threshold

        start = time.perf_counter()

        # Embed query
        query_embedding = await self._embedding_service.embed_query(query)

        # Vector search
        hits = await self._vector_store.search(
            query_embedding,
            top_k=top_k,
            collection=collection,
            threshold=threshold,
        )

        elapsed_ms = (time.perf_counter() - start) * 1000

        # Format results
        results = []
        for doc, score in hits:
            results.append({
                "document_id": doc.metadata.get("document_id", ""),
                "content": doc.page_content,
                "score": round(score, 4),
                "metadata": {
                    k: v
                    for k, v in doc.metadata.items()
                    if k not in ("document_id",)
                },
            })

        logger.info(
            "Search: query='%s...', top_k=%d, found=%d, time=%.1fms",
            query[:50], top_k, len(results), elapsed_ms,
        )

        return {
            "query": query,
            "total_results": len(results),
            "results": results,
            "search_time_ms": round(elapsed_ms, 2),
        }

"""Abstract base class for vector store implementations.

Defines the contract that both Milvus and Chroma stores must fulfill.
All methods are async to support non-blocking vector operations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from langchain_core.documents import Document


class BaseVectorStore(ABC):
    """Abstract interface for vector store operations.

    Implementations: MilvusStore, ChromaStore.
    """

    @abstractmethod
    async def add_documents(
        self, documents: list[Document], collection: str | None = None,
        embeddings: list[list[float]] | None = None,
    ) -> list[str]:
        """Embed and store documents, returning their chunk IDs.

        Args:
            documents: List of LangChain Document objects with page_content and metadata.
            collection: Target collection name. Uses default if None.

        Returns:
            List of generated chunk IDs.
        """
        ...

    @abstractmethod
    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        collection: str | None = None,
        threshold: float | None = None,
    ) -> list[tuple[Document, float]]:
        """Search for similar documents by embedding vector.

        Args:
            query_embedding: The query vector.
            top_k: Maximum number of results to return.
            collection: Collection name. Uses default if None.
            threshold: Minimum similarity score. No filtering if None.

        Returns:
            List of (Document, score) tuples sorted by descending similarity.
        """
        ...

    @abstractmethod
    async def delete(
        self, doc_ids: list[str], collection: str | None = None
    ) -> int:
        """Delete documents by their IDs.

        Args:
            doc_ids: List of document/chunk IDs to remove.
            collection: Collection name. Uses default if None.

        Returns:
            Number of documents actually deleted.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the vector store is reachable and healthy.

        Returns:
            True if the store is operational.
        """
        ...

    @abstractmethod
    async def get_collection_stats(self, collection: str | None = None) -> dict:
        """Get statistics for the specified collection.

        Args:
            collection: Collection name. Uses default if None.

        Returns:
            Dict with keys like 'name', 'count', 'dimension'.
        """
        ...

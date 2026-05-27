"""Chroma vector store implementation for local development.

Uses chromadb PersistentClient for on-disk persistence. Provides the same
interface as MilvusStore so switching requires only a config change.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_core.documents import Document

from src.app.core.config import Settings
from src.app.vectorstore.base import BaseVectorStore

logger = logging.getLogger(__name__)


class ChromaStore(BaseVectorStore):
    """Chroma-backed vector store for local development.

    Keeps data in a persistent directory so it survives restarts.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._persist_dir = settings.chroma_persist_dir
        self._default_collection = settings.chroma_collection_name
        self._dimension = settings.milvus_dimension
        self._client: chromadb.PersistentClient | None = None

    def _get_client(self) -> chromadb.PersistentClient:
        """Lazy-init the Chroma persistent client."""
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=self._persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            logger.info("Chroma client initialized at %s", self._persist_dir)
        return self._client

    def _get_or_create_collection(self, collection_name: str) -> Any:
        """Get or create a Chroma collection."""
        client = self._get_client()
        try:
            return client.get_collection(collection_name)
        except Exception:
            logger.info("Creating Chroma collection '%s'", collection_name)
            return client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )

    async def add_documents(
        self, documents: list[Document], collection: str | None = None
    ) -> list[str]:
        col_name = collection or self._default_collection
        col = self._get_or_create_collection(col_name)

        chunk_ids: list[str] = []
        texts: list[str] = []
        metadatas: list[dict] = []

        for doc in documents:
            cid = str(uuid.uuid4())
            chunk_ids.append(cid)
            texts.append(doc.page_content)
            metadatas.append({**doc.metadata, "chunk_id": cid})

        col.add(documents=texts, metadatas=metadatas, ids=chunk_ids)
        logger.info("Added %d chunks to Chroma collection '%s'", len(chunk_ids), col_name)
        return chunk_ids

    async def add_embeddings(
        self,
        chunk_ids: list[str],
        embeddings: list[list[float]],
        collection: str | None = None,
    ) -> None:
        col_name = collection or self._default_collection
        col = self._get_or_create_collection(col_name)

        # Update existing documents with embeddings
        col.update(ids=chunk_ids, embeddings=embeddings)
        logger.info("Updated %d embeddings in Chroma collection '%s'", len(chunk_ids), col_name)

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        collection: str | None = None,
        threshold: float | None = None,
    ) -> list[tuple[Document, float]]:
        col_name = collection or self._default_collection
        col = self._get_or_create_collection(col_name)

        results = col.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        output: list[tuple[Document, float]] = []
        if not results["ids"][0]:
            return output

        for i, doc_id in enumerate(results["ids"][0]):
            distance = results["distances"][0][i]
            # Convert cosine distance to similarity score
            score = 1.0 - (distance / 2.0)

            if threshold is not None and score < threshold:
                continue

            doc = Document(
                page_content=results["documents"][0][i] or "",
                metadata=results["metadatas"][0][i] if results["metadatas"] else {},
            )
            output.append((doc, score))

        return output

    async def delete(self, doc_ids: list[str], collection: str | None = None) -> int:
        col_name = collection or self._default_collection
        col = self._get_or_create_collection(col_name)

        # Chroma doesn't have a direct "delete by doc_id" — we query first
        all_ids = col.get()["ids"]
        to_delete = [did for did in doc_ids if did in all_ids]
        if to_delete:
            col.delete(ids=to_delete)
        logger.info("Deleted %d chunks from Chroma", len(to_delete))
        return len(to_delete)

    async def health_check(self) -> bool:
        try:
            self._get_client()
            return True
        except Exception:
            logger.exception("Chroma health check failed")
            return False

    async def get_collection_stats(self, collection: str | None = None) -> dict:
        col_name = collection or self._default_collection
        try:
            col = self._get_or_create_collection(col_name)
            return {"name": col_name, "count": col.count(), "dimension": self._dimension}
        except Exception:
            return {"name": col_name, "count": 0}

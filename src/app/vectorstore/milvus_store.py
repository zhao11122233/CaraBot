"""Milvus vector store implementation.

Wraps pymilvus sync API with asyncio.to_thread for non-blocking operations.
Supports collection auto-creation with IVF_FLAT or HNSW index on 1024-dim vectors.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from langchain_core.documents import Document
from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    MilvusClient,
    connections,
    utility,
)

from src.app.core.config import Settings
from src.app.core.exceptions import VectorStoreException
from src.app.vectorstore.base import BaseVectorStore

logger = logging.getLogger(__name__)

# Milvus field names
ID_FIELD = "id"
VECTOR_FIELD = "embedding"
TEXT_FIELD = "text"
DOC_ID_FIELD = "doc_id"
METADATA_FIELD = "metadata"


class MilvusStore(BaseVectorStore):
    """Milvus-backed vector store for production use.

    Uses the pymilvus Orm and Collections API. All sync operations are
    wrapped in asyncio.to_thread to avoid blocking the async event loop.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._host = settings.milvus_host
        self._port = settings.milvus_port
        self._user = settings.milvus_user
        self._password = settings.milvus_password
        self._default_collection = settings.milvus_collection_name
        self._dimension = settings.milvus_dimension
        self._client: MilvusClient | None = None
        self._connected = False

    async def _ensure_connected(self) -> None:
        """Connect to Milvus if not already connected. Runs in thread pool."""
        if self._connected:
            return

        def _connect() -> None:
            connections.connect(
                alias="default",
                host=self._host,
                port=self._port,
                user=self._user,
                password=self._password,
            )

        await asyncio.to_thread(_connect)
        self._client = MilvusClient(uri=f"http://{self._host}:{self._port}")
        self._connected = True
        logger.info("Connected to Milvus at %s:%s", self._host, self._port)

    def _get_collection(self, collection_name: str) -> Collection:
        """Get or create a Milvus collection with the standard CaraBot schema."""
        if not utility.has_collection(collection_name):
            return self._create_collection(collection_name)
        return Collection(collection_name)

    def _create_collection(self, collection_name: str) -> Collection:
        """Create a new collection with the standard schema and index."""
        fields = [
            FieldSchema(name=ID_FIELD, dtype=DataType.VARCHAR, max_length=128, is_primary=True),
            FieldSchema(name=VECTOR_FIELD, dtype=DataType.FLOAT_VECTOR, dim=self._dimension),
            FieldSchema(name=TEXT_FIELD, dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name=DOC_ID_FIELD, dtype=DataType.VARCHAR, max_length=128),
            FieldSchema(name=METADATA_FIELD, dtype=DataType.JSON),
        ]
        schema = CollectionSchema(fields, description="CaraBot knowledge base")
        collection = Collection(collection_name, schema=schema)

        # Build FLAT index (exact search, suitable for all dataset sizes)
        index_params = {
            "metric_type": "IP",
            "index_type": "FLAT",
            "params": {},
        }
        collection.create_index(VECTOR_FIELD, index_params)
        collection.load()
        logger.info("Created Milvus collection '%s' (dim=%s)", collection_name, self._dimension)
        return collection

    async def add_documents(
        self, documents: list[Document], collection: str | None = None,
        embeddings: list[list[float]] | None = None,
    ) -> list[str]:
        await self._ensure_connected()
        col_name = collection or self._default_collection

        chunk_ids: list[str] = []
        data_rows: list[dict[str, Any]] = []

        for i, doc in enumerate(documents):
            chunk_id = str(uuid.uuid4())
            chunk_ids.append(chunk_id)
            data_rows.append({
                ID_FIELD: chunk_id,
                VECTOR_FIELD: embeddings[i] if embeddings else [],
                TEXT_FIELD: doc.page_content,
                DOC_ID_FIELD: doc.metadata.get("document_id", ""),
                METADATA_FIELD: doc.metadata,
            })

        def _insert() -> None:
            col = self._get_collection(col_name)
            col.insert(data_rows)
            col.flush()

        await asyncio.to_thread(_insert)
        logger.info("Inserted %d chunks into Milvus collection '%s'", len(chunk_ids), col_name)
        return chunk_ids

    async def add_embeddings(
        self,
        chunk_ids: list[str],
        embeddings: list[list[float]],
        collection: str | None = None,
    ) -> None:
        """Insert pre-computed embeddings with their chunk IDs into Milvus.

        This is the recommended path: embed with BGE-m3 externally, then
        call this method to store the resulting vectors.
        """
        await self._ensure_connected()
        col_name = collection or self._default_collection

        def _upsert() -> None:
            col = self._get_collection(col_name)
            rows = [
                {ID_FIELD: cid, VECTOR_FIELD: emb}
                for cid, emb in zip(chunk_ids, embeddings)
            ]
            col.upsert(rows)
            col.flush()

        await asyncio.to_thread(_upsert)
        logger.info("Upserted %d embeddings into Milvus collection '%s'", len(chunk_ids), col_name)

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        collection: str | None = None,
        threshold: float | None = None,
    ) -> list[tuple[Document, float]]:
        await self._ensure_connected()
        col_name = collection or self._default_collection

        def _search() -> list[dict]:
            col = self._get_collection(col_name)
            col.load()
            search_params = {"metric_type": "IP", "params": {"nprobe": 16}}
            results = col.search(
                data=[query_embedding],
                anns_field=VECTOR_FIELD,
                param=search_params,
                limit=top_k,
                output_fields=[TEXT_FIELD, DOC_ID_FIELD, METADATA_FIELD],
            )
            return results[0]  # first (only) query

        hits = await asyncio.to_thread(_search)

        results: list[tuple[Document, float]] = []
        for hit in hits:
            score = float(hit.score)
            if threshold is not None and score < threshold:
                continue
            doc = Document(
                page_content=hit.entity.get(TEXT_FIELD, ""),
                metadata={
                    "chunk_id": hit.id,
                    "document_id": hit.entity.get(DOC_ID_FIELD, ""),
                    **hit.entity.get(METADATA_FIELD, {}),
                },
            )
            results.append((doc, score))

        return results

    async def delete(self, doc_ids: list[str], collection: str | None = None) -> int:
        await self._ensure_connected()
        col_name = collection or self._default_collection

        def _delete() -> int:
            col = self._get_collection(col_name)
            expr = f'{DOC_ID_FIELD} in {json.dumps(doc_ids)}'
            result = col.delete(expr)
            col.flush()
            return result.delete_count if result else 0

        import json
        count = await asyncio.to_thread(_delete)
        logger.info("Deleted %d chunks from Milvus for doc_ids=%s", count, doc_ids)
        return count

    async def health_check(self) -> bool:
        try:
            await self._ensure_connected()
            return utility.get_server_version() is not None
        except Exception:
            logger.exception("Milvus health check failed")
            return False

    async def get_collection_stats(self, collection: str | None = None) -> dict:
        await self._ensure_connected()
        col_name = collection or self._default_collection

        def _stats() -> dict:
            if not utility.has_collection(col_name):
                return {"name": col_name, "count": 0}
            col = self._get_collection(col_name)
            return {
                "name": col_name,
                "count": col.num_entities,
                "dimension": self._dimension,
            }

        return await asyncio.to_thread(_stats)

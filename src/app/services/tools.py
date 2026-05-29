"""LangGraph tool definitions wrapping existing CaraBot services.

Each tool returns a formatted string for LLM consumption. The factory function
create_tools() follows the same dependency injection pattern used by routers.
"""

from __future__ import annotations

import logging
from typing import Annotated

from langchain_core.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---- Tool input schemas ----

class SearchToolInput(BaseModel):
    """Input schema for search_knowledge_base tool."""

    query: str = Field(..., description="Search query text")
    top_k: int = Field(default=5, description="Number of results to return")
    threshold: float = Field(default=0.7, description="Minimum similarity score (0.0-1.0)")
    collection: str | None = Field(default=None, description="Collection name to search in")


class IngestTextInput(BaseModel):
    """Input schema for ingest_text tool."""

    text: str = Field(..., description="Text content to ingest into the knowledge base")
    title: str = Field(..., description="Document title or filename for the ingested text")
    author: str | None = Field(default=None, description="Document author")
    collection: str | None = Field(default=None, description="Target collection name")


# ---- Tool factory ----

def create_tools(search_service, stats_service, upload_service) -> list:
    """Create LangGraph-compatible async tool functions wrapping existing services.

    Returns a list of callable tools suitable for binding to an LLM via .bind_tools().
    """

    @tool(args_schema=SearchToolInput)
    async def search_knowledge_base(
        query: str,
        top_k: int = 5,
        threshold: float = 0.7,
        collection: str | None = None,
    ) -> str:
        """Search the knowledge base for relevant document chunks.

        Use when the user asks a question that requires retrieving information
        from indexed documents. Returns matching chunks with scores and metadata.
        """
        result = await search_service.search(
            query=query, top_k=top_k, threshold=threshold, collection=collection,
        )
        if result["total_results"] == 0:
            return "No relevant documents found in the knowledge base."

        lines = [
            f"Found {result['total_results']} results (search took {result['search_time_ms']}ms):"
        ]
        for i, r in enumerate(result["results"], 1):
            lines.append(
                f"\n--- Result {i} (score: {r['score']}, doc_id: {r['document_id']}) ---\n"
                f"{r['content']}"
            )
        return "\n".join(lines)

    @tool
    async def get_knowledge_base_stats() -> str:
        """Get statistics about the knowledge base.

        Use when the user asks about document counts, chunk counts, available
        collections, or the last time documents were indexed.
        """
        result = await stats_service.get_stats()
        lines = [
            "Knowledge Base Statistics:",
            f"- Total documents: {result['total_documents']}",
            f"- Total chunks: {result['total_chunks']}",
            f"- Vector store: {result['vector_store_type']}",
            f"- Last updated: {result['last_updated'] or 'N/A'}",
        ]
        for col in result.get("collections", []):
            lines.append(
                f"- Collection '{col['collection_name']}': "
                f"{col['document_count']} docs, {col['chunk_count']} chunks"
            )
        return "\n".join(lines)

    @tool(args_schema=IngestTextInput)
    async def ingest_text(
        text: str,
        title: str,
        author: str | None = None,
        collection: str | None = None,
    ) -> str:
        """Ingest text content as a new document into the knowledge base.

        Use when the user wants to save information, add a note, or store text
        content for future retrieval. The text is chunked, embedded, and indexed.
        """
        content_bytes = text.encode("utf-8")
        filename = title if title.endswith(".txt") else f"{title}.txt"

        result = await upload_service.upload(
            file_content=content_bytes,
            filename=filename,
            mime_type="text/plain",
            author=author,
            collection=collection,
        )
        return (
            f"Successfully ingested '{result['filename']}' "
            f"(doc_id: {result['document_id']}, "
            f"chunks: {result['chunk_count']}, "
            f"duplicate: {result['is_duplicate']})."
        )

    return [search_knowledge_base, get_knowledge_base_stats, ingest_text]

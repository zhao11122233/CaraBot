"""Pydantic request/response models for the CaraBot API."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# --- Health ---

class ComponentHealth(BaseModel):
    """Health status of a single dependency component."""

    status: str = Field(..., description="up | down")
    detail: str | None = Field(default=None, description="Additional info or error message")


class HealthResponse(BaseModel):
    """GET /health response body."""

    status: str = Field(..., description="up | down — overall service status")
    checks: dict[str, ComponentHealth] = Field(
        default_factory=dict, description="Per-component health checks"
    )


# --- Upload ---

class UploadResponse(BaseModel):
    """POST /api/v1/upload response body."""

    document_id: str = Field(..., description="UUID of the stored document")
    filename: str = Field(..., description="Original file name")
    file_hash: str = Field(..., description="SHA256 hash of the file content")
    file_size: int = Field(..., description="File size in bytes")
    chunk_count: int = Field(..., description="Number of text chunks created")
    is_duplicate: bool = Field(
        default=False, description="True if this file was already indexed"
    )
    message: str = Field(default="Document processed successfully.")


# --- Search ---

class SearchRequest(BaseModel):
    """POST /api/v1/search request body."""

    query: str = Field(..., min_length=1, max_length=4096, description="Search query text")
    top_k: int = Field(default=5, ge=1, le=100, description="Number of results to return")
    threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Minimum similarity score"
    )
    collection: str | None = Field(
        default=None, description="Vector store collection name; uses default if not set"
    )


class SearchResult(BaseModel):
    """A single search result with content and score."""

    document_id: str = Field(..., description="Source document UUID")
    content: str = Field(..., description="Chunk text content")
    score: float = Field(..., description="Similarity score (0.0–1.0)")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Document metadata (filename, etc.)"
    )


class SearchResponse(BaseModel):
    """POST /api/v1/search response body."""

    query: str = Field(..., description="Original search query")
    total_results: int = Field(..., description="Number of results returned")
    results: list[SearchResult] = Field(default_factory=list)
    search_time_ms: float = Field(..., description="Search duration in milliseconds")


# --- Stats ---

class CollectionStats(BaseModel):
    """Statistics for a single vector store collection."""

    collection_name: str
    document_count: int
    chunk_count: int


class StatsResponse(BaseModel):
    """GET /api/v1/stats response body."""

    total_documents: int = Field(..., description="Total indexed documents across all collections")
    total_chunks: int = Field(..., description="Total chunks across all collections")
    collections: list[CollectionStats] = Field(default_factory=list)
    vector_store_type: str = Field(..., description="Active vector store backend")
    last_updated: datetime | None = Field(
        default=None, description="Timestamp of most recent document indexing"
    )


# --- Error ---

class ErrorDetail(BaseModel):
    """Standard error response body."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error description")
    trace_id: str = Field(default="", description="Request trace ID for debugging")


class ErrorResponse(BaseModel):
    """Wrapper for all error responses."""

    error: ErrorDetail

"""Tests for the chat endpoint and agent tools.

Verifies:
- Chat endpoint requires auth
- Non-streaming chat returns correct response structure
- Streaming chat returns SSE events
- thread_id is returned and can be reused
- Tools produce correct output format
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# ---- Mock AgentService ----

def _make_mock_agent_service():
    """Create a mock AgentService that returns canned responses."""
    mock = MagicMock()
    mock.run = AsyncMock(return_value={
        "thread_id": "test-thread-uuid",
        "message": "I found 3 documents about knowledge retrieval.",
        "tool_calls": [
            {"tool_name": "search_knowledge_base", "arguments": {"query": "knowledge retrieval"}, "result_summary": None}
        ],
    })
    mock.stream = MagicMock()
    mock.shutdown = AsyncMock()
    return mock


# ---- Tools Tests ----

class TestTools:
    """Tests for tool functions wrapping existing services."""

    async def test_search_knowledge_base_returns_formatted_results(self):
        """search_knowledge_base should return a formatted string with results."""
        from src.app.services.tools import create_tools

        search_svc = MagicMock()
        search_svc.search = AsyncMock(return_value={
            "query": "test",
            "total_results": 2,
            "results": [
                {"document_id": "doc-1", "content": "Content A", "score": 0.95, "metadata": {}},
                {"document_id": "doc-2", "content": "Content B", "score": 0.82, "metadata": {}},
            ],
            "search_time_ms": 12.5,
        })
        stats_svc = MagicMock()
        upload_svc = MagicMock()

        tools = create_tools(search_svc, stats_svc, upload_svc)
        tool = next(t for t in tools if t.name == "search_knowledge_base")
        result = await tool.ainvoke({"query": "test"})

        assert "Found 2 results" in result
        assert "Content A" in result
        assert "doc-1" in result
        assert "0.95" in result

    async def test_search_knowledge_base_empty_results(self):
        """search_knowledge_base should handle no results."""
        from src.app.services.tools import create_tools

        search_svc = MagicMock()
        search_svc.search = AsyncMock(return_value={
            "query": "nothing", "total_results": 0, "results": [], "search_time_ms": 5.0,
        })
        stats_svc = MagicMock()
        upload_svc = MagicMock()

        tools = create_tools(search_svc, stats_svc, upload_svc)
        tool = next(t for t in tools if t.name == "search_knowledge_base")
        result = await tool.ainvoke({"query": "nothing"})

        assert "No relevant documents found" in result

    async def test_get_knowledge_base_stats_returns_formatted_counts(self):
        """get_knowledge_base_stats should return formatted statistics."""
        from src.app.services.tools import create_tools

        search_svc = MagicMock()
        stats_svc = MagicMock()
        stats_svc.get_stats = AsyncMock(return_value={
            "total_documents": 42,
            "total_chunks": 1530,
            "collections": [
                {"collection_name": "carabot_knowledge", "document_count": 42, "chunk_count": 1530},
            ],
            "vector_store_type": "milvus",
            "last_updated": "2026-05-01T12:00:00",
        })
        upload_svc = MagicMock()

        tools = create_tools(search_svc, stats_svc, upload_svc)
        tool = next(t for t in tools if t.name == "get_knowledge_base_stats")
        result = await tool.ainvoke({})

        assert "42" in result
        assert "1530" in result
        assert "milvus" in result
        assert "carabot_knowledge" in result

    async def test_ingest_text_returns_success_message(self):
        """ingest_text should call upload service and return success."""
        from src.app.services.tools import create_tools

        search_svc = MagicMock()
        stats_svc = MagicMock()
        upload_svc = MagicMock()
        upload_svc.upload = AsyncMock(return_value={
            "document_id": "new-doc-id",
            "filename": "mynote.txt",
            "file_hash": "abc123",
            "file_size": 100,
            "chunk_count": 3,
            "is_duplicate": False,
            "message": "Document processed successfully.",
        })

        tools = create_tools(search_svc, stats_svc, upload_svc)
        tool = next(t for t in tools if t.name == "ingest_text")
        result = await tool.ainvoke({"text": "Hello world", "title": "mynote"})

        assert "Successfully ingested" in result
        assert "mynote.txt" in result
        assert "new-doc-id" in result
        assert "duplicate: False" in result


# ---- Chat Endpoint Tests ----

class TestChatEndpoint:
    """Tests for POST /api/v1/chat."""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock AgentService for the chat endpoint."""
        return _make_mock_agent_service()

    @pytest.fixture
    def app_with_chat(self, mock_agent):
        """Create test app with mocked AgentService."""
        from src.app.core.config import load_settings
        from src.app.core.logging import setup_logging
        from src.app.models import Base
        from sqlalchemy.ext.asyncio import create_async_engine
        import asyncio

        settings = load_settings()
        setup_logging(settings)

        # Ensure tables exist
        async def _create_tables():
            engine = create_async_engine(settings.db_url, echo=False)
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            await engine.dispose()

        asyncio.get_event_loop().run_until_complete(_create_tables())

        from src.app.main import create_app
        with (
            patch("src.app.main.get_vector_store"),
            patch("src.app.main.EmbeddingService"),
            patch("src.app.main.AgentService", return_value=mock_agent),
        ):
            app = create_app()
        return app

    @pytest.fixture
    async def chat_client(self, app_with_chat):
        """Async HTTP client for chat tests."""
        from httpx import ASGITransport
        transport = ASGITransport(app=app_with_chat)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    async def test_chat_requires_auth(self, chat_client: AsyncClient) -> None:
        """Chat without auth should be rejected."""
        response = await chat_client.post(
            "/api/v1/chat",
            json={"message": "Hello"},
            headers={},
        )
        assert response.status_code in (400, 401)

    async def test_chat_returns_response_structure(
        self, chat_client: AsyncClient, auth_headers: dict
    ) -> None:
        """Non-streaming chat should return thread_id, message, and tool_calls."""
        response = await chat_client.post(
            "/api/v1/chat",
            json={"message": "What documents do I have?"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "thread_id" in data
        assert "message" in data
        assert "tool_calls" in data
        assert isinstance(data["tool_calls"], list)
        assert data["thread_id"] == "test-thread-uuid"

    async def test_chat_with_thread_id(
        self, chat_client: AsyncClient, auth_headers: dict
    ) -> None:
        """Chat with existing thread_id should be accepted."""
        response = await chat_client.post(
            "/api/v1/chat",
            json={"message": "Tell me more", "thread_id": "existing-thread-123"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["thread_id"] == "test-thread-uuid"

    async def test_chat_empty_message_rejected(
        self, chat_client: AsyncClient, auth_headers: dict
    ) -> None:
        """Empty message should return validation error."""
        response = await chat_client.post(
            "/api/v1/chat",
            json={"message": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_chat_streaming_returns_sse(
        self, mock_agent, app_with_chat, auth_headers: dict
    ) -> None:
        """Streaming chat should return SSE events."""
        # Configure mock stream to yield events
        async def mock_stream(message, thread_id=None):
            yield {"event": "token", "data": "Hello"}
            yield {"event": "token", "data": " world"}
            yield {"event": "done", "data": {"thread_id": "stream-thread-123"}}

        mock_agent.stream = mock_stream

        from httpx import ASGITransport
        transport = ASGITransport(app=app_with_chat)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat",
                json={"message": "Hi", "stream": True},
                headers=auth_headers,
            )
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")

    async def test_chat_tool_calls_in_response(
        self, chat_client: AsyncClient, auth_headers: dict
    ) -> None:
        """Response tool_calls should include tool_name and arguments."""
        response = await chat_client.post(
            "/api/v1/chat",
            json={"message": "Search for AI safety"},
            headers=auth_headers,
        )
        data = response.json()
        for tc in data["tool_calls"]:
            assert "tool_name" in tc
            assert "arguments" in tc


# ---- Schemas Tests ----

class TestChatSchemas:
    """Tests for chat request/response validation."""

    def test_chat_request_valid(self):
        """Valid ChatRequest should parse correctly."""
        from src.app.models.chat_schemas import ChatRequest
        req = ChatRequest(message="Hello", thread_id=None, stream=False)
        assert req.message == "Hello"
        assert req.thread_id is None
        assert req.stream is False

    def test_chat_request_message_too_long(self):
        """ChatRequest with excessively long message should fail."""
        from pydantic import ValidationError
        from src.app.models.chat_schemas import ChatRequest
        with pytest.raises(ValidationError):
            ChatRequest(message="x" * 20000, thread_id=None)

    def test_chat_response_structure(self):
        """ChatResponse should serialize correctly."""
        from src.app.models.chat_schemas import ChatResponse, ToolCallDetail
        resp = ChatResponse(
            thread_id="tid-1",
            message="Hello!",
            tool_calls=[
                ToolCallDetail(tool_name="search", arguments={"q": "test"})
            ],
        )
        data = resp.model_dump()
        assert data["thread_id"] == "tid-1"
        assert data["message"] == "Hello!"
        assert len(data["tool_calls"]) == 1

"""Shared test fixtures for CaraBot.

Provides:
- In-memory SQLite database (no PostgreSQL needed)
- Mock vector store (no Milvus/Chroma needed)
- Mock embedding service (fast, deterministic)
- Test HTTP client configured with the app
"""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.app.models import Base

# Force test configuration before importing app modules
os.environ["API_KEY"] = "test-api-key"
os.environ["VECTOR_STORE_TYPE"] = "chroma"
os.environ["DB_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["BGE_MODEL_PATH"] = "/tmp/test-models/bge-m3"
os.environ["LOG_FILE"] = "/dev/null"
os.environ["LOG_FORMAT"] = "text"


@pytest.fixture
def test_db_url() -> str:
    """In-memory SQLite URL for tests."""
    return "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_engine_and_session(test_db_url: str):
    """Create an async SQLAlchemy engine with in-memory SQLite."""
    engine = create_async_engine(test_db_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    yield engine, session_factory

    await engine.dispose()


@pytest.fixture
async def db_session(db_engine_and_session) -> AsyncGenerator[AsyncSession, None]:
    """Yield a single async database session."""
    _, session_factory = db_engine_and_session
    async with session_factory() as session:
        yield session


@pytest.fixture
def mock_vector_store() -> MagicMock:
    """Mock vector store that records adds and returns fake search results."""
    store = MagicMock()
    store.add_documents = AsyncMock(return_value=[str(uuid.uuid4())])
    store.add_embeddings = AsyncMock(return_value=None)
    store.search = AsyncMock(return_value=[])
    store.delete = AsyncMock(return_value=1)
    store.health_check = AsyncMock(return_value=True)
    store.get_collection_stats = AsyncMock(
        return_value={"name": "test", "count": 0, "dimension": 1024}
    )
    return store


@pytest.fixture
def mock_embedding_service() -> MagicMock:
    """Mock embedding service that returns fake 1024-dim vectors."""
    service = MagicMock()
    service.embed_query = AsyncMock(return_value=[0.1] * 1024)
    service.embed_documents = AsyncMock(return_value=[[0.1] * 1024])
    service.health_check = AsyncMock(return_value=True)
    service.startup = AsyncMock(return_value=None)
    return service


@pytest.fixture
def app_with_mocks(mock_vector_store, mock_embedding_service):
    """Create a FastAPI test app with mocked dependencies."""
    from src.app.core.config import load_settings
    from src.app.core.logging import setup_logging
    from src.app.main import create_app

    setup_logging(load_settings())

    # Override the create_app to use mocks
    from unittest.mock import patch

    with (
        patch("src.app.main.get_vector_store", return_value=mock_vector_store),
        patch("src.app.main.EmbeddingService", return_value=mock_embedding_service),
    ):
        app = create_app()
    return app


@pytest.fixture
async def test_client(app_with_mocks):
    """Async HTTP test client with the app transport."""
    transport = ASGITransport(app=app_with_mocks)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Valid auth headers for test requests."""
    return {"X-API-Key": "test-api-key"}


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Minimal PDF bytes for testing."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n"
        b"0000000115 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF"
    )


@pytest.fixture
def sample_txt_bytes() -> bytes:
    """Sample text content for testing."""
    return b"This is a test document about knowledge retrieval systems.\n" * 10

"""SQLAlchemy database models and session management."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.app.core.config import Settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


def create_engine_and_session(settings: Settings):
    """Create async SQLAlchemy engine and session factory from settings.

    Conditionally applies pooling options for PostgreSQL; skips them for SQLite.
    """
    is_sqlite = "sqlite" in settings.db_url

    engine_kwargs = {"echo": False}
    if not is_sqlite:
        engine_kwargs.update({
            "pool_size": 10,
            "max_overflow": 20,
            "pool_pre_ping": True,
        })

    engine = create_async_engine(settings.db_url, **engine_kwargs)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return engine, session_factory

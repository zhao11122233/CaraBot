#!/usr/bin/env python3
"""Database initialization script.

Creates all required PostgreSQL tables and ensures Milvus collections exist.
Run before starting the application for the first time.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import load_settings
from app.models import Base


async def init_database() -> None:
    """Create all tables in PostgreSQL."""
    settings = load_settings()
    print(f"Connecting to database: {settings.db_url}")

    engine = create_async_engine(settings.db_url, echo=True)

    async with engine.begin() as conn:
        # Create all tables defined in SQLAlchemy models
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created successfully.")

    # Verify tables exist
    async with engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' ORDER BY table_name"
            )
        )
        tables = [row[0] for row in result.fetchall()]
        print(f"Existing tables: {', '.join(tables) if tables else 'none'}")

    await engine.dispose()
    print("Database initialization complete.")


async def init_milvus() -> None:
    """Verify Milvus connection and create default collection if needed."""
    settings = load_settings()
    if settings.vector_store_type != "milvus":
        print("Vector store is not Milvus, skipping.")
        return

    try:
        from pymilvus import connections, utility
        connections.connect(
            host=settings.milvus_host,
            port=settings.milvus_port,
            user=settings.milvus_user,
            password=settings.milvus_password,
        )
        version = utility.get_server_version()
        print(f"Connected to Milvus v{version}")

        collections = utility.list_collections()
        print(f"Existing collections: {collections}")

        if settings.milvus_collection_name not in collections:
            print(
                f"Collection '{settings.milvus_collection_name}' "
                f"will be auto-created on first use."
            )
        else:
            print(f"Collection '{settings.milvus_collection_name}' exists.")
    except Exception as exc:
        print(f"Warning: Milvus initialization failed: {exc}")
        print("The collection will be created automatically on first use.")


async def main() -> None:
    """Run all initialization steps."""
    print("=" * 60)
    print("CaraBot Database Initialization")
    print("=" * 60)

    await init_database()
    print()
    await init_milvus()

    print()
    print("Done. Start the application with:")
    print("  uvicorn src.app.main:create_app --factory --reload")


if __name__ == "__main__":
    asyncio.run(main())

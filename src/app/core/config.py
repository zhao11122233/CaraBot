"""Application configuration via Pydantic Settings.

All configuration values are loaded from environment variables or .env file.
Validation runs at startup — missing required values produce clear error messages.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for CaraBot. All fields populated from env/.env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
    )

    # --- API Authentication ---
    api_key: str = Field(..., min_length=8, description="API Key for request authentication")

    # --- Vector Store ---
    vector_store_type: Literal["milvus", "chroma"] = Field(
        default="milvus", description="Vector store backend: milvus or chroma"
    )

    # Milvus
    milvus_host: str = Field(default="localhost", description="Milvus server hostname")
    milvus_port: int = Field(default=19530, ge=1, le=65535, description="Milvus server port")
    milvus_user: str = Field(default="root", description="Milvus username")
    milvus_password: str = Field(default="Milvus", description="Milvus password")
    milvus_collection_name: str = Field(
        default="carabot_knowledge", description="Default Milvus collection name"
    )
    milvus_dimension: int = Field(
        default=1024, description="Vector dimension (1024 for BGE-m3)"
    )

    # Chroma
    chroma_persist_dir: str = Field(
        default="./data/chroma", description="Directory for Chroma persistent storage"
    )
    chroma_collection_name: str = Field(
        default="carabot_knowledge", description="Default Chroma collection name"
    )

    # --- Embedding Model ---
    bge_model_name: str = Field(
        default="BAAI/bge-m3", description="HuggingFace model identifier for BGE-m3"
    )
    bge_model_path: str = Field(
        default="./data/models/bge-m3",
        description="Local directory for model caching; auto-download if missing",
    )
    bge_device: str = Field(default="cpu", description="Device for model inference: cpu | cuda")
    bge_batch_size: int = Field(default=32, ge=1, le=256, description="Batch size for embeddings")

    # --- Database ---
    db_url: str = Field(
        default="postgresql+asyncpg://carabot:carabot@localhost:5432/carabot",
        description="Async PostgreSQL connection string (asyncpg driver)",
    )
    db_url_sync: str = Field(
        default="postgresql+psycopg2://carabot:carabot@localhost:5432/carabot",
        description="Synchronous PostgreSQL connection string for migrations",
    )

    # --- Redis ---
    redis_url: str = Field(
        default="redis://localhost:6379/0", description="Redis connection URL"
    )
    redis_index_queue: str = Field(
        default="carabot:index:queue", description="Redis queue name for indexing tasks"
    )

    # --- Document Processing ---
    chunk_size: int = Field(
        default=500, ge=100, le=10000, description="Text chunk size for splitting"
    )
    chunk_overlap: int = Field(
        default=50, ge=0, le=1000, description="Overlap between adjacent chunks"
    )
    max_file_size: int = Field(
        default=52_428_800, ge=1, description="Maximum upload file size in bytes (default 50MB)"
    )

    # --- Retrieval ---
    top_k: int = Field(default=5, ge=1, le=100, description="Default number of results to return")
    similarity_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Minimum similarity score threshold"
    )

    # --- Logging ---
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", description="Logging level"
    )
    log_file: str = Field(default="./logs/carabot.log", description="Log file path")
    log_format: Literal["json", "text"] = Field(
        default="json", description="Log output format: json or text"
    )

    # --- LLM Configuration ---
    llm_base_url: str = Field(
        default="http://localhost:8000/v1",
        description="OpenAI-compatible API base URL (OpenAI, DeepSeek, Qwen, vLLM, etc.)",
    )
    llm_api_key: str = Field(
        default="not-needed",
        description="API key for the LLM provider",
    )
    llm_model: str = Field(
        default="gpt-4o-mini",
        description="Model name for the OpenAI-compatible API",
    )
    llm_temperature: float = Field(
        default=0.1, ge=0.0, le=2.0, description="LLM temperature for response generation"
    )
    llm_max_tokens: int = Field(
        default=2048, ge=1, le=16384, description="Maximum tokens in LLM response"
    )

    # --- Agent Configuration ---
    agent_max_iterations: int = Field(
        default=10, ge=1, le=50,
        description="Maximum number of agent reasoning loops",
    )
    agent_system_prompt: str = Field(
        default=(
            "You are CaraBot, a helpful RAG-based knowledge assistant. "
            "You can search the knowledge base, check document statistics, "
            "and ingest new text documents. "
            "Always cite specific documents when answering from search results. "
            "Be concise and accurate."
        ),
        description="System prompt for the LangGraph agent",
    )
    agent_checkpoint_db_url: str = Field(
        default="",
        description="Sync PostgreSQL URL for LangGraph checkpoints. "
                    "Defaults to a derived sync URL from DB_URL if left empty.",
    )

    # --- Server ---
    host: str = Field(default="0.0.0.0", description="Server bind address")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    workers: int = Field(default=4, ge=1, le=16, description="Number of uvicorn workers")

    @field_validator("api_key")
    @classmethod
    def api_key_must_not_be_default(cls, v: str) -> str:
        """Warn but don't block if API key looks like a default value."""
        if v in ("change-me", "changeme", "your-api-key-here"):
            raise ValueError(
                "API_KEY is set to an insecure default value. "
                "Please set a strong API_KEY in your .env file."
            )
        return v

    @field_validator("db_url")
    @classmethod
    def db_url_must_be_valid_async_driver(cls, v: str) -> str:
        """Ensure the DB URL uses an async driver (asyncpg or aiosqlite)."""
        valid_drivers = ("asyncpg", "aiosqlite", "sqlite+aiosqlite")
        if not any(d in v for d in valid_drivers):
            raise ValueError(
                f"DB_URL must use an async driver (postgresql+asyncpg://... or "
                f"sqlite+aiosqlite://...), got: {v}"
            )
        return v

    @field_validator("chroma_persist_dir", "log_file", "bge_model_path")
    @classmethod
    def ensure_parent_dirs_exist(cls, v: str) -> str:
        """Create parent directories for file/directory paths at validation time."""
        path = Path(v)
        if not path.is_absolute() and not v.startswith("./"):
            pass  # relative paths are fine
        return v

    @field_validator("chunk_overlap")
    @classmethod
    def overlap_less_than_chunk_size(cls, v: int, info) -> int:
        """Ensure chunk_overlap is smaller than chunk_size."""
        chunk_size = info.data.get("chunk_size", 0)
        if v >= chunk_size:
            raise ValueError(
                f"CHUNK_OVERLAP ({v}) must be less than CHUNK_SIZE ({chunk_size})"
            )
        return v

    @field_validator("milvus_user", "milvus_host")
    @classmethod
    def milvus_config_required_when_milvus_selected(cls, v: str, info) -> str:
        """Ensure Milvus config is provided when Milvus is the selected store."""
        store_type = info.data.get("vector_store_type", "chroma")
        if store_type == "milvus" and not v:
            raise ValueError(
                f"Field '{info.field_name}' is required when VECTOR_STORE_TYPE=milvus"
            )
        return v


def load_settings() -> Settings:
    """Load and validate all settings. Exits with a clear message on failure."""
    try:
        settings = Settings()
    except ValidationError as exc:
        print("=" * 60)
        print("CONFIGURATION ERROR: Missing or invalid configuration values")
        print("=" * 60)
        for error in exc.errors():
            loc = " -> ".join(str(x) for x in error["loc"])
            msg = error["msg"]
            print(f"  [{loc}] {msg}")
        print("=" * 60)
        print("Fix the issues above in your .env file and restart.")
        print("See .env.example for all required variables.")
        raise SystemExit(1) from exc

    # Create necessary directories
    for dir_path in [
        settings.chroma_persist_dir,
        settings.bge_model_path,
        os.path.dirname(settings.log_file),
    ]:
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)

    return settings

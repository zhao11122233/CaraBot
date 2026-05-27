"""Vector store factory — returns the configured backend."""

from __future__ import annotations

from src.app.core.config import Settings
from src.app.core.exceptions import ConfigurationException
from src.app.vectorstore.base import BaseVectorStore
from src.app.vectorstore.chroma_store import ChromaStore
from src.app.vectorstore.milvus_store import MilvusStore


def get_vector_store(settings: Settings) -> BaseVectorStore:
    """Factory: return the vector store instance based on configuration.

    Args:
        settings: Validated application settings.

    Returns:
        Concrete BaseVectorStore implementation.

    Raises:
        ConfigurationException: If VECTOR_STORE_TYPE is unrecognized.
    """
    store_type = settings.vector_store_type.lower()

    if store_type == "milvus":
        return MilvusStore(settings)
    elif store_type == "chroma":
        return ChromaStore(settings)
    else:
        raise ConfigurationException(
            f"Unsupported VECTOR_STORE_TYPE '{store_type}'. "
            f"Must be one of: milvus, chroma."
        )

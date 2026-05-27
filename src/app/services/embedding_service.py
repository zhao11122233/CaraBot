"""BGE-m3 multi-language embedding service.

Loads the BAAI/bge-m3 model from local cache or downloads from HuggingFace.
Provides batch embedding for documents and single query embedding.
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

from src.app.core.config import Settings
from src.app.core.exceptions import EmbeddingException

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Wraps the BGE-m3 sentence-transformer model for async embedding."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._model_name = settings.bge_model_name
        self._model_path = settings.bge_model_path
        self._device = settings.bge_device
        self._batch_size = settings.bge_batch_size
        self._model = None

    def _load_model(self):
        """Load the BGE-m3 model. Called once at startup."""
        from sentence_transformers import SentenceTransformer

        model_path = self._resolve_model_path()
        logger.info("Loading embedding model from %s", model_path)
        self._model = SentenceTransformer(
            model_path,
            device=self._device,
            trust_remote_code=True,
        )

        # Warm up with a dummy inference
        _ = self._model.encode(["warmup"], batch_size=1, normalize_embeddings=True)
        dim = self._model.get_sentence_embedding_dimension()
        logger.info("Embedding model loaded. Dimension: %s", dim)

    def _resolve_model_path(self) -> str:
        """Return the local model path, downloading if necessary."""
        local_dir = Path(self._model_path)
        if local_dir.exists() and any(local_dir.iterdir()):
            logger.info("Using cached model at %s", local_dir)
            return str(local_dir)

        # Create parent directory
        local_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Downloading model %s to %s", self._model_name, local_dir)
        try:
            from sentence_transformers import SentenceTransformer
            # Download to the local directory
            model = SentenceTransformer(self._model_name, trust_remote_code=True)
            model.save(str(local_dir))
            logger.info("Model saved to %s", local_dir)
        except Exception as exc:
            raise EmbeddingException(
                f"Failed to download model '{self._model_name}': {exc}"
            ) from exc

        return str(local_dir)

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of document texts.

        Args:
            texts: List of text chunks to embed.

        Returns:
            List of embedding vectors, each being a list of floats.
        """
        if not self._model:
            raise EmbeddingException("Model not loaded. Call startup() first.")

        if not texts:
            return []

        try:
            embeddings = await asyncio.to_thread(
                self._model.encode,
                texts,
                batch_size=self._batch_size,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return embeddings.tolist()
        except Exception as exc:
            raise EmbeddingException(f"Document embedding failed: {exc}") from exc

    async def embed_query(self, text: str) -> list[float]:
        """Embed a single search query.

        Args:
            text: The query string.

        Returns:
            Embedding vector as a list of floats.
        """
        if not self._model:
            raise EmbeddingException("Model not loaded. Call startup() first.")

        try:
            embedding = await asyncio.to_thread(
                self._model.encode,
                [text],
                batch_size=1,
                normalize_embeddings=True,
            )
            return embedding[0].tolist()
        except Exception as exc:
            raise EmbeddingException(f"Query embedding failed: {exc}") from exc

    async def startup(self) -> None:
        """Load the model. Call once during application startup."""
        await asyncio.to_thread(self._load_model)

    async def health_check(self) -> bool:
        """Verify the model is loaded and can perform inference."""
        if self._model is None:
            return False
        try:
            _ = await self.embed_query("health check")
            return True
        except Exception:
            logger.exception("Embedding model health check failed")
            return False

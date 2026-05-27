"""Document loading, parsing, and text splitting.

Supports PDF, DOCX, Markdown, and TXT formats with configurable
chunk_size and chunk_overlap via LangChain text splitters.
"""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from pathlib import Path
from typing import BinaryIO

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.app.core.config import Settings
from src.app.core.exceptions import DocumentException, UnsupportedFileTypeException

logger = logging.getLogger(__name__)

SUPPORTED_MIMETYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/msword": ".doc",
    "text/markdown": ".md",
    "text/plain": ".txt",
    "text/x-markdown": ".md",
}

# Additional extension-based mapping for clients that don't send proper MIME
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".md", ".txt", ".markdown"}


class DocumentProcessor:
    """Loads documents from various formats and splits them into chunks."""

    def __init__(self, settings: Settings) -> None:
        self._chunk_size = settings.chunk_size
        self._chunk_overlap = settings.chunk_overlap
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
            separators=["\n\n", "\n", "。", ".", " ", ""],
            length_function=len,
        )

    def _infer_mime_type(self, filename: str) -> str:
        """Infer MIME type from file extension."""
        ext = Path(filename).suffix.lower()
        mapping = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".md": "text/markdown",
            ".markdown": "text/markdown",
            ".txt": "text/plain",
        }
        mime = mapping.get(ext)
        if not mime:
            raise UnsupportedFileTypeException(
                f"Unsupported file extension '{ext}' for file '{filename}'. "
                f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )
        return mime

    async def load_and_split(
        self, file_content: bytes, filename: str, mime_type: str | None = None
    ) -> list[Document]:
        """Load a document from raw bytes and split into chunks.

        Args:
            file_content: Raw file bytes.
            filename: Original filename (used for extension detection).
            mime_type: MIME type. Auto-detected from filename if None.

        Returns:
            List of LangChain Document chunks with metadata.

        Raises:
            UnsupportedFileTypeException: If file format is not supported.
            DocumentException: If parsing fails.
        """
        if mime_type is None:
            mime_type = self._infer_mime_type(filename)

        ext = Path(filename).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS and mime_type not in SUPPORTED_MIMETYPES:
            raise UnsupportedFileTypeException(
                f"Unsupported format '{mime_type}' for file '{filename}'."
            )

        # Write to temp file for LangChain loaders
        suffix = ext or ".tmp"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name

        try:
            documents = await asyncio.to_thread(self._load_file, tmp_path, mime_type)
        except Exception as exc:
            raise DocumentException(
                f"Failed to parse '{filename}': {exc}"
            ) from exc
        finally:
            os.unlink(tmp_path)

        # Add source metadata to each chunk
        for doc in documents:
            doc.metadata.setdefault("source", filename)
            doc.metadata.setdefault("mime_type", mime_type)

        chunks = await asyncio.to_thread(self._splitter.split_documents, documents)
        logger.info(
            "Processed '%s': %d document(s) → %d chunks (chunk_size=%d, overlap=%d)",
            filename, len(documents), len(chunks), self._chunk_size, self._chunk_overlap,
        )
        return chunks

    def _load_file(self, file_path: str, mime_type: str) -> list[Document]:
        """Load a file using the appropriate LangChain loader. Runs in thread pool."""
        if mime_type == "application/pdf":
            from langchain_community.document_loaders import PyPDFLoader
            loader = PyPDFLoader(file_path)
            return loader.load()

        elif mime_type in (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        ):
            from langchain_community.document_loaders import Docx2txtLoader
            loader = Docx2txtLoader(file_path)
            return loader.load()

        elif mime_type in ("text/markdown", "text/x-markdown"):
            from langchain_community.document_loaders import UnstructuredMarkdownLoader
            try:
                loader = UnstructuredMarkdownLoader(file_path)
                return loader.load()
            except ImportError:
                # Fallback to plain text if unstructured is not available
                from langchain_community.document_loaders import TextLoader
                loader = TextLoader(file_path, encoding="utf-8")
                return loader.load()

        elif mime_type == "text/plain":
            from langchain_community.document_loaders import TextLoader
            loader = TextLoader(file_path, encoding="utf-8")
            return loader.load()

        else:
            raise UnsupportedFileTypeException(f"Cannot load mime type: {mime_type}")

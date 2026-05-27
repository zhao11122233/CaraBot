"""JSON logging configuration with trace_id support.

Provides structured JSON logging to both console and file, with automatic
trace_id injection via contextvars for distributed request tracing.
"""

from __future__ import annotations

import logging
import os
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

import json

from src.app.core.config import Settings

# Context variable for per-request trace ID
_trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")


def get_trace_id() -> str:
    """Return the current request's trace_id, or empty string if not in a request."""
    return _trace_id_var.get()


def set_trace_id(trace_id: str | None = None) -> str:
    """Set a trace_id for the current context. Generates a new UUID if none provided."""
    tid = trace_id or str(uuid.uuid4())
    _trace_id_var.set(tid)
    return tid


class JSONFormatter(logging.Formatter):
    """Formats log records as JSON lines with trace_id, timestamp, and module info."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": f"{record.module}:{record.lineno}",
            "message": record.getMessage(),
            "trace_id": get_trace_id(),
        }

        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False, default=str)


class TextFormatter(logging.Formatter):
    """Standard text log format with trace_id for local development."""

    def __init__(self) -> None:
        super().__init__(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(module)s:%(lineno)d | "
            "trace_id=%(trace_id)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )

    def format(self, record: logging.LogRecord) -> str:
        record.trace_id = get_trace_id()  # type: ignore[attr-defined]
        return super().format(record)


def setup_logging(settings: Settings) -> None:
    """Configure the root logger with JSON and console handlers.

    Should be called once at application startup before any logging occurs.
    """
    root = logging.getLogger()
    root.setLevel(getattr(logging, settings.log_level))

    # Remove any existing handlers (idempotent)
    root.handlers.clear()

    # Choose formatter based on config
    if settings.log_format == "json":
        formatter: logging.Formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    # File handler
    log_dir = os.path.dirname(settings.log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    file_handler = logging.FileHandler(settings.log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    # Silence noisy third-party loggers
    for noisy_logger in ("asyncio", "urllib3", "botocore", "httpx", "chromadb", "pymilvus"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)

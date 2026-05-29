"""Pydantic models for the chat API."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """POST /api/v1/chat request body."""

    message: str = Field(..., min_length=1, max_length=16384, description="User message")
    thread_id: str | None = Field(
        default=None,
        description="Conversation thread ID. Omit to start a new conversation.",
    )
    stream: bool = Field(
        default=False, description="If true, response is streamed as SSE events."
    )


class ToolCallDetail(BaseModel):
    """Metadata about a tool invocation within the agent's reasoning."""

    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    result_summary: str | None = None


class ChatResponse(BaseModel):
    """POST /api/v1/chat response body (non-streaming)."""

    thread_id: str = Field(..., description="Conversation thread ID")
    message: str = Field(..., description="Agent's text response")
    tool_calls: list[ToolCallDetail] = Field(
        default_factory=list, description="Tools called during reasoning"
    )

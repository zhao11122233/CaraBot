"""POST /api/v1/chat — Conversational agent endpoint with SSE streaming support."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from src.app.middleware.auth import AuthGuard
from src.app.models.chat_schemas import ChatRequest, ChatResponse, ToolCallDetail
from src.app.services.agent_service import AgentService

logger = logging.getLogger(__name__)


def create_chat_router(
    auth_guard: AuthGuard,
    agent_service: AgentService,
) -> APIRouter:
    """Factory for the chat router with injected dependencies."""
    router = APIRouter(tags=["Chat"])

    @router.post("/chat", response_model=ChatResponse)
    async def chat(
        body: ChatRequest,
        _api_key: str = Depends(auth_guard),
    ):
        """Send a message to the CaraBot agent.

        The agent can search the knowledge base, check statistics, and ingest
        text as needed to answer queries. Pass a thread_id to continue an
        existing conversation.
        """
        if body.stream:
            async def event_generator():
                async for event in agent_service.stream(
                    message=body.message, thread_id=body.thread_id,
                ):
                    yield {"event": event["event"], "data": event["data"]}

            return EventSourceResponse(event_generator())

        result = await agent_service.run(
            message=body.message, thread_id=body.thread_id,
        )
        return ChatResponse(
            thread_id=result["thread_id"],
            message=result["message"],
            tool_calls=[ToolCallDetail(**tc) for tc in result.get("tool_calls", [])],
        )

    return router

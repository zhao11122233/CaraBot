"""Agent and LLM exception classes for the LangGraph integration."""

from __future__ import annotations

from src.app.core.exceptions import CaraBotException


class AgentException(CaraBotException):
    """Base exception for agent/LangGraph errors."""

    code = "AGENT_ERROR"
    status_code = 500
    message = "Agent execution failed."


class LLMException(AgentException):
    """LLM API call failure (network, rate limit, model error)."""

    code = "LLM_ERROR"
    status_code = 502
    message = "LLM service error."


class ToolExecutionException(AgentException):
    """A tool called by the agent failed during execution."""

    code = "TOOL_ERROR"
    status_code = 500
    message = "Tool execution failed."


class ConversationNotFoundException(AgentException):
    """Requested conversation thread_id not found in checkpoints."""

    code = "CONVERSATION_NOT_FOUND"
    status_code = 404
    message = "Conversation thread not found."

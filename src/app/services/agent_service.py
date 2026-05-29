"""LangGraph agent service: graph construction, checkpointing, and execution.

Provides both non-streaming (run) and streaming (stream) execution of the
ReAct agent graph, with conversation state persisted to PostgreSQL.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, AsyncIterator, TypedDict, Annotated

from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI

from src.app.core.config import Settings
from src.app.core.agent_exceptions import AgentException, LLMException

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State schema for the ReAct agent graph. messages is the only key;
    add_messages handles appending, dedup, and ID-based merging."""
    messages: Annotated[list, add_messages]


class AgentService:
    """Wraps LangGraph agent graph creation, checkpointing, and execution."""

    def __init__(
        self,
        settings: Settings,
        tools: list,
        search_service,
        stats_service,
        upload_service,
    ) -> None:
        self._settings = settings
        self._tools = tools
        self._search_service = search_service
        self._stats_service = stats_service
        self._upload_service = upload_service

        self._model = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            openai_api_key=settings.llm_api_key,
            openai_api_base=settings.llm_base_url.rstrip("/"),
        )
        self._model_with_tools = self._model.bind_tools(self._tools)

        self._graph: CompiledStateGraph | None = None
        self._checkpointer = None

    async def startup(self) -> None:
        """Initialize checkpoint storage and compile the agent graph."""
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

        checkpoint_url = self._settings.agent_checkpoint_db_url or (
            self._settings.db_url.replace(
                "postgresql+asyncpg://", "postgresql://"
            )
        )
        self._checkpointer = AsyncPostgresSaver.from_conn_string(checkpoint_url)
        await self._checkpointer.setup()
        self._graph = self._build_graph()
        logger.info(
            "AgentService started: model=%s, tools=%d",
            self._settings.llm_model, len(self._tools),
        )

    async def shutdown(self) -> None:
        """Close checkpoint connections. The AsyncPostgresSaver manages its own pool."""
        if self._checkpointer is not None:
            self._checkpointer = None
        self._graph = None

    def _build_graph(self) -> CompiledStateGraph:
        """Build the ReAct agent graph: model node ⇄ tools node loop."""

        async def call_model(state: AgentState, config: RunnableConfig) -> dict:
            messages = state["messages"]
            response = await self._model_with_tools.ainvoke(messages, config)
            return {"messages": [response]}

        async def call_tools(state: AgentState, config: RunnableConfig) -> dict:
            last_message = state["messages"][-1]
            tool_messages: list[ToolMessage] = []

            for tool_call in last_message.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_fn = next((t for t in self._tools if t.name == tool_name), None)

                if tool_fn is None:
                    tool_messages.append(ToolMessage(
                        content=f"Error: Unknown tool '{tool_name}'",
                        tool_call_id=tool_call["id"],
                    ))
                    continue

                try:
                    result = await tool_fn.ainvoke(tool_args, config)
                    tool_messages.append(ToolMessage(
                        content=str(result),
                        tool_call_id=tool_call["id"],
                    ))
                except Exception as exc:
                    logger.exception("Tool '%s' failed", tool_name)
                    tool_messages.append(ToolMessage(
                        content=f"Tool execution error: {exc}",
                        tool_call_id=tool_call["id"],
                    ))

            return {"messages": tool_messages}

        def should_continue(state: AgentState) -> str:
            last_message = state["messages"][-1]
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                return "call_tools"
            return END

        workflow = StateGraph(AgentState)
        workflow.add_node("call_model", call_model)
        workflow.add_node("call_tools", call_tools)
        workflow.set_entry_point("call_model")
        workflow.add_conditional_edges("call_model", should_continue, {
            "call_tools": "call_tools",
            END: END,
        })
        workflow.add_edge("call_tools", "call_model")

        return workflow.compile(checkpointer=self._checkpointer)

    async def run(
        self, message: str, thread_id: str | None = None,
    ) -> dict:
        """Execute the agent non-streaming.

        Returns a dict with thread_id, message, and tool_calls metadata.
        """
        if self._graph is None:
            raise AgentException("Agent not initialized. Call startup() first.")

        tid = thread_id or str(uuid.uuid4())
        config: RunnableConfig = {
            "configurable": {"thread_id": tid},
            "recursion_limit": self._settings.agent_max_iterations,
        }

        input_state = {
            "messages": [
                SystemMessage(content=self._settings.agent_system_prompt),
                HumanMessage(content=message),
            ],
        }

        try:
            result = await self._graph.ainvoke(input_state, config)
        except Exception as exc:
            logger.exception("Agent execution failed for thread %s", tid)
            raise LLMException(f"Agent execution failed: {exc}") from exc

        final_message = result["messages"][-1]
        tool_calls_meta = self._extract_tool_calls(result["messages"])

        return {
            "thread_id": tid,
            "message": final_message.content if hasattr(final_message, "content") else str(final_message),
            "tool_calls": tool_calls_meta,
        }

    async def stream(
        self, message: str, thread_id: str | None = None,
    ) -> AsyncIterator[dict]:
        """Execute the agent with streaming. Yields SSE-style event dicts.

        Event types: token, tool_call_start, tool_call_end, done, error.
        """
        if self._graph is None:
            yield {"event": "error", "data": "Agent not initialized."}
            return

        tid = thread_id or str(uuid.uuid4())
        config: RunnableConfig = {
            "configurable": {"thread_id": tid},
            "recursion_limit": self._settings.agent_max_iterations,
        }

        input_state = {
            "messages": [
                SystemMessage(content=self._settings.agent_system_prompt),
                HumanMessage(content=message),
            ],
        }

        try:
            async for event in self._graph.astream_events(input_state, config, version="v2"):
                kind = event["event"]
                if kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        yield {"event": "token", "data": content}
                elif kind == "on_tool_start":
                    yield {
                        "event": "tool_call_start",
                        "data": {
                            "tool_name": event["name"],
                            "input": event["data"].get("input"),
                        },
                    }
                elif kind == "on_tool_end":
                    yield {
                        "event": "tool_call_end",
                        "data": {
                            "tool_name": event["name"],
                            "output": str(event["data"].get("output", ""))[:512],
                        },
                    }
            yield {"event": "done", "data": {"thread_id": tid}}
        except Exception as exc:
            logger.exception("Agent streaming failed for thread %s", tid)
            yield {"event": "error", "data": str(exc)}

    def _extract_tool_calls(self, messages: list) -> list[dict]:
        """Extract tool call metadata from message history for response serialization."""
        tool_calls = []
        for msg in messages:
            if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
                for tc in msg.tool_calls:
                    tool_calls.append({
                        "tool_name": tc["name"],
                        "arguments": tc["args"],
                        "result_summary": None,
                    })
        return tool_calls

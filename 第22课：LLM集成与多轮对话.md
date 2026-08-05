# CaraBot Agent 智能知识库系统课程
## 第 22 课：LLM 集成与多轮对话

### 🎯 本节课目标
- 掌握 OpenAI 兼容接口的使用（ChatOpenAI + bind_tools）
- 理解流式（SSE）与非流式响应的实现差异
- 深入学习对话状态管理（Checkpoint 持久化）
- 学会对接多种 LLM 提供商（OpenAI、DeepSeek、Qwen、本地模型）
- 学习时长：3 天
- 实践任务：实现多轮对话并验证状态恢复

---

## 1. OpenAI 兼容接口

### 1.1 为什么用 OpenAI 兼容接口？

几乎所有的 LLM 提供商都支持 OpenAI 兼容的 API 格式，这让 CaraBot 可以**改一行配置就切换模型**：

```python
self._model = ChatOpenAI(
    model=settings.llm_model,          # "gpt-4o-mini"
    temperature=settings.llm_temperature,  # 0.1
    max_tokens=settings.llm_max_tokens,    # 2048
    openai_api_key=settings.llm_api_key,   # "sk-..."
    openai_api_base=settings.llm_base_url, # "https://api.openai.com/v1"
)
```

### 1.2 支持的提供商

| 提供商 | llm_base_url | llm_model | llm_api_key |
|--------|-------------|-----------|-------------|
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` | `sk-...` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` | API Key |
| Qwen (通义千问) | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-turbo` | API Key |
| 本地 vLLM | `http://localhost:8000/v1` | `qwen2:7b` | `not-needed` |
| 本地 Ollama | `http://localhost:11434/v1` | `llama3:8b` | `not-needed` |

### 1.3 bind_tools：工具绑定

```python
self._model_with_tools = self._model.bind_tools(self._tools)
```

`bind_tools` 在每次发给 LLM 的请求中自动附加工具定义。LLM 返回的响应中如果包含 `tool_calls`，说明 LLM 想调用工具。

---

## 2. 非流式响应（run）

### 2.1 实现

```python
async def run(self, message: str, thread_id=None) -> dict:
    tid = thread_id or str(uuid.uuid4())
    config = {
        "configurable": {"thread_id": tid},
        "recursion_limit": self._settings.agent_max_iterations,
    }
    input_state = {
        "messages": [
            SystemMessage(content=self._settings.agent_system_prompt),
            HumanMessage(content=message),
        ],
    }

    result = await self._graph.ainvoke(input_state, config)

    final_message = result["messages"][-1]
    tool_calls_meta = self._extract_tool_calls(result["messages"])

    return {
        "thread_id": tid,
        "message": final_message.content,
        "tool_calls": tool_calls_meta,
    }
```

### 2.2 响应格式

```json
{
  "thread_id": "abc-123-def",
  "message": "根据知识库，RAG 是检索增强生成（Retrieval-Augmented Generation）的缩写...",
  "tool_calls": [
    {
      "tool_name": "search_knowledge_base",
      "arguments": {"query": "什么是RAG", "top_k": 5, "threshold": 0.7},
      "result_summary": null
    }
  ]
}
```

---

## 3. 流式响应（stream + SSE）

### 3.1 为什么需要流式？

非流式：用户等 5 秒 → 一次返回整段回复
流式：用户看到回复在"一个字一个字"地出现（像 ChatGPT 那样）

### 3.2 实现

```python
async def stream(self, message: str, thread_id=None) -> AsyncIterator[dict]:
    tid = thread_id or str(uuid.uuid4())
    config = {
        "configurable": {"thread_id": tid},
        "recursion_limit": self._settings.agent_max_iterations,
    }
    input_state = {
        "messages": [
            SystemMessage(content=self._settings.agent_system_prompt),
            HumanMessage(content=message),
        ],
    }

    async for event in self._graph.astream_events(input_state, config, version="v2"):
        kind = event["event"]

        if kind == "on_chat_model_stream":
            # LLM 在逐 token 生成
            content = event["data"]["chunk"].content
            if content:
                yield {"event": "token", "data": content}

        elif kind == "on_tool_start":
            # 工具开始执行
            yield {
                "event": "tool_call_start",
                "data": {
                    "tool_name": event["name"],
                    "input": event["data"].get("input"),
                },
            }

        elif kind == "on_tool_end":
            # 工具执行完毕
            yield {
                "event": "tool_call_end",
                "data": {
                    "tool_name": event["name"],
                    "output": str(event["data"].get("output", ""))[:512],
                },
            }

    yield {"event": "done", "data": {"thread_id": tid}}
```

### 3.3 SSE 事件类型

| 事件 | 含义 | data 内容 |
|------|------|----------|
| `token` | LLM 生成的一个 token | `"RAG"`, `"是"`, `"检索"`, ... |
| `tool_call_start` | 开始执行工具 | `{tool_name, input}` |
| `tool_call_end` | 工具执行完成 | `{tool_name, output}` |
| `done` | 对话结束 | `{thread_id}` |
| `error` | 出错 | 错误信息 |

### 3.4 API 层的 SSE 响应

```python
@router.post("/chat")
async def chat(body: ChatRequest, _api_key: str = Depends(auth_guard)):
    if body.stream:
        async def event_generator():
            async for event in agent_service.stream(body.message, body.thread_id):
                yield {"event": event["event"], "data": event["data"]}

        return EventSourceResponse(event_generator())

    result = await agent_service.run(body.message, body.thread_id)
    return ChatResponse(...)
```

### 3.5 前端消费 SSE

```javascript
const eventSource = new EventSource('/api/v1/chat?stream=true');

eventSource.addEventListener('token', (e) => {
    // 逐字显示
    document.getElementById('output').innerText += JSON.parse(e.data);
});

eventSource.addEventListener('tool_call_start', (e) => {
    // 显示"正在搜索知识库..."
});

eventSource.addEventListener('done', (e) => {
    // 对话结束，保存 thread_id 用于后续对话
    const { thread_id } = JSON.parse(e.data);
});
```

---

## 4. 多轮对话与 Checkpoint

### 4.1 对话状态持久化

```python
# LangGraph 自动把每个节点执行后的状态存到 PostgreSQL
async def startup(self):
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    checkpoint_url = self._settings.agent_checkpoint_db_url or (
        self._settings.db_url.replace("postgresql+asyncpg://", "postgresql://")
    )
    self._checkpointer = AsyncPostgresSaver.from_conn_string(checkpoint_url)
    await self._checkpointer.setup()  # 自动创建 checkpoints 表
```

### 4.2 多轮对话示例

```
第 1 轮：
  POST /chat {"message": "知识库里有几份文档？"}
  → thread_id: "t-001"
  → Agent 调用 get_knowledge_base_stats
  → 回答："有 42 份文档"
  → State 自动持久化

第 2 轮：
  POST /chat {"message": "最新的是哪份？", "thread_id": "t-001"}
  → LangGraph 从 PostgreSQL 恢复之前的 State
  → Agent 知道上下文：刚才在讨论文档数量
  → 调用 search_knowledge_base("latest document")
  → 回答："最新的是 '2024年度报告.pdf'，上传于 2024-03-15"
```

### 4.3 Checkpoint 的存储结构

LangGraph 在 PostgreSQL 中创建的 `checkpoints` 表：

```sql
-- 伪结构
{
  "thread_id": "t-001",
  "checkpoint_id": "1ef9...",
  "parent_checkpoint_id": "1ef8...",
  "checkpoint": {
    "messages": [
      SystemMessage(...),
      HumanMessage("知识库里有几份文档？"),
      AIMessage(tool_calls=[...]),
      ToolMessage("42 份文档"),
      AIMessage("有 42 份文档"),
      HumanMessage("最新的是哪份？"),    ← 第 2 轮追加的消息
    ]
  }
}
```

---

## 5. System Prompt 工程

### 5.1 CaraBot 的默认 Prompt

```python
agent_system_prompt: str = Field(default=(
    "You are CaraBot, a helpful RAG-based knowledge assistant. "
    "You can search the knowledge base, check document statistics, "
    "and ingest new text documents. "
    "Always cite specific documents when answering from search results. "
    "Be concise and accurate."
))
```

### 5.2 Prompt 调优建议

```python
# 更好的 Prompt（有更多行为约束）
AGENT_SYSTEM_PROMPT = """You are CaraBot, an enterprise knowledge base assistant.

Capabilities:
- Search the knowledge base using search_knowledge_base
- Check document statistics using get_knowledge_base_stats
- Save text content using ingest_text

Rules:
1. Always search the knowledge base before answering factual questions.
2. Cite specific document IDs and scores when using search results.
3. If search returns no results, tell the user clearly.
4. Answer in the same language as the user's question.
5. Be concise — prefer 1-3 sentences unless the user asks for detail.
6. If you're unsure, say so rather than guessing.
"""
```

---

## 6. 课后作业

1. **切换 LLM 提供商**：将 CaraBot 从 OpenAI 切换到 DeepSeek，验证功能正常
2. **流式体验**：用 curl 测试 SSE 流式接口，观察 token 级别的输出
3. **多轮对话测试**：创建 thread，连续发送 3 条相关消息，验证 Checkpoint 能否正确恢复上下文
4. **System Prompt 实验**：修改 `agent_system_prompt`，加入"请用古诗词风格回答"，观察效果
5. **错误处理测试**：故意配置错误的 API Key，观察 AgentService 如何处理 LLM 调用失败
6. **对比流式 vs 非流式**：测量同一个问题的首字节时间（TTFB）和总耗时

---

## 📚 扩展阅读
- OpenAI API 文档：https://platform.openai.com/docs/api-reference
- Server-Sent Events：https://html.spec.whatwg.org/multipage/server-sent-events.html
- LangGraph Streaming：https://langchain-ai.github.io/langgraph/how-tos/streaming/
- DeepSeek API：https://platform.deepseek.com/api-docs/

---

**下节课预告**：第 23 课 - 多格式文档支持（PDF、DOCX、Markdown 解析与扩展）

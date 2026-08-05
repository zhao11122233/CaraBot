# CaraBot Agent 智能知识库系统课程
## 第 27 课：Agent 进阶与多模型适配

### 🎯 本节课目标
- 掌握 Agent System Prompt 工程的进阶技巧
- 学会适配多种 LLM 提供商（OpenAI、DeepSeek、Qwen、本地模型）
- 理解 Tool 调用失败的处理与重试策略
- 学习时长：3 天
- 实践任务：切换 LLM 提供商并对比 Agent 表现

---

## 1. System Prompt 工程进阶

### 1.1 好 Prompt 的结构

```
① 角色定义：你是谁
② 能力说明：你能做什么
③ 行为规则：你怎么做
④ 格式要求：你的输出长什么样
⑤ 边界约束：你不能做什么
```

### 1.2 CaraBot 进阶 Prompt 示例

```python
ADVANCED_SYSTEM_PROMPT = """You are CaraBot, an enterprise knowledge base assistant for Carlcare AICC.

## Capabilities
- search_knowledge_base: Search indexed documents with semantic similarity.
- get_knowledge_base_stats: Query document and chunk statistics.
- ingest_text: Save text content into the knowledge base.

## Rules
1. SEARCH FIRST: Always search the knowledge base before answering factual questions.
   Never answer from your own training data alone.
2. CITE SOURCES: When using search results, mention the document filename and relevance score.
   Example: "According to 'HR_Policy_2024.pdf' (relevance: 95%)..."
3. EMPTY RESULTS: If search returns no results, say: "I couldn't find relevant information
   in the knowledge base. You may want to upload related documents first."
4. LANGUAGE: Reply in the same language as the user's question.
5. CONCISENESS: Keep answers under 3 sentences unless the user asks for detail.
6. UNCERTAINTY: If you're unsure, say so clearly. Never fabricate information.
7. INGESTION: Only use ingest_text when the user explicitly asks to save something.

## Format
- For factual answers: Direct answer + citation
- For statistics: Bullet points
- For errors: Clear error message + suggested next step

## Constraints
- Maximum 10 reasoning steps per conversation.
- Each search returns at most 5 chunks.
- You cannot delete, modify, or list individual documents.
"""
```

### 1.3 Prompt 调优的迭代流程

```
① 写初版 Prompt
② 跑 10 个典型场景，记录 Agent 行为
③ 找出不符合预期的行为（如：没查知识库就直接回答、回答太长）
④ 在 Prompt 中加对应规则
⑤ 重新测试 → 确认改善
⑥ 迭代 ②-⑤ 直到满意
```

---

## 2. 多 LLM 提供商适配

### 2.1 配置切换

```bash
# OpenAI
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-xxxx
LLM_MODEL=gpt-4o-mini

# DeepSeek
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_API_KEY=sk-xxxx
LLM_MODEL=deepseek-chat

# Qwen (阿里通义千问)
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_API_KEY=sk-xxxx
LLM_MODEL=qwen-turbo

# 本地 Ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=not-needed
LLM_MODEL=qwen2:7b
```

### 2.2 不同模型的工具调用能力

| 模型 | 工具调用 | 中文 | 推理能力 | 速度 | 费用 |
|------|---------|------|---------|------|------|
| gpt-4o-mini | ✅ 强 | ✅ | ✅ | 快 | 低 |
| gpt-4o | ✅ 很强 | ✅ | ✅ | 中 | 高 |
| deepseek-chat | ✅ 强 | ✅✅ | ✅ | 中 | 很低 |
| qwen-turbo | ✅ 中 | ✅✅ | ✅ | 快 | 很低 |
| qwen2:7b (本地) | ⚠️ 弱 | ✅ | ⚠️ | 取决于 GPU | 免费 |
| llama3:8b (本地) | ⚠️ 弱 | ⚠️ | ⚠️ | 取决于 GPU | 免费 |

### 2.3 模型选择决策树

```
需要高精度回答？
  ├── YES → GPT-4o / DeepSeek-Chat
  └── NO → 需要低成本？
            ├── YES → DeepSeek / Qwen（API）
            └── NO → 需要数据不出内网？
                      ├── YES → 本地部署 Qwen2 / Llama3
                      └── NO → GPT-4o-mini
```

---

## 3. Tool 调用失败处理

### 3.1 失败场景

```python
# 场景 1：工具不存在
LLM 要调用 "delete_all_documents" → 工具列表里没有 → 返回错误消息

# 场景 2：工具执行抛异常
search_knowledge_base("...") → EmbeddingException → 返回错误消息

# 场景 3：递归死循环
LLM 不断调用工具... → recursion_limit 达到 → 抛出异常
```

### 3.2 CaraBot 的容错实现

```python
async def call_tools(state: AgentState, config: RunnableConfig) -> dict:
    tool_messages = []
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_fn = next((t for t in self._tools if t.name == tool_name), None)

        if tool_fn is None:
            # 工具不存在 → 返回错误提示
            tool_messages.append(ToolMessage(
                content=f"Error: Unknown tool '{tool_name}'. Available: {[t.name for t in self._tools]}",
                tool_call_id=tool_call["id"],
            ))
            continue

        try:
            result = await tool_fn.ainvoke(tool_call["args"], config)
            tool_messages.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))
        except Exception as exc:
            logger.exception("Tool '%s' failed", tool_name)
            # 工具执行失败 → 返回错误消息，让 LLM 决定下一步
            tool_messages.append(ToolMessage(
                content=f"Tool execution error: {exc}. Try a different approach.",
                tool_call_id=tool_call["id"],
            ))

    return {"messages": tool_messages}
```

**关键设计**：工具报错不会让整个对话崩溃。错误消息作为 ToolMessage 返回给 LLM，LLM 看到错误后会调整策略（比如换一种搜索关键词、告诉用户出了问题等）。

### 3.3 重试策略

```python
# 对于网络瞬断等可重试的错误，可以在工具层面加重试
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

@tool(args_schema=SearchToolInput)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
async def search_knowledge_base(query, top_k=5, threshold=0.7):
    result = await search_service.search(query=query, top_k=top_k, threshold=threshold)
    # ...
```

---

## 4. 课后作业

1. **Prompt 对比实验**：用默认 Prompt 和进阶 Prompt 各测试 5 个相同问题，对比 Agent 的行为差异
2. **多模型切换**：依次切换到 OpenAI、DeepSeek、Qwen，测试工具调用成功率
3. **失败测试**：故意让工具执行失败（如断网、错误参数），观察 Agent 如何处理
4. **多模型打分**：设计 10 个评估问题，分别用不同模型回答，从准确性、引用质量、响应速度三个维度打分

---

## 📚 扩展阅读
- OpenAI Function Calling Best Practices：https://platform.openai.com/docs/guides/function-calling
- DeepSeek API：https://platform.deepseek.com/api-docs
- Prompt Engineering Guide：https://www.promptingguide.ai/

---

**下节课预告**：第 28 课 - 容器化部署（Docker 镜像构建、Docker Compose 编排）

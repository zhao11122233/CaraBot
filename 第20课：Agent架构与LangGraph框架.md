# CaraBot Agent 智能知识库系统课程
## 第 20 课：Agent 架构与 LangGraph 框架

### 🎯 本节课目标
- 理解 Agent 的设计理念与 ReAct（Reasoning + Acting）模式
- 掌握 LangGraph StateGraph 的核心概念：State、Node、Edge、Conditional Edge
- 深入分析 CaraBot 的 Agent 图结构（call_model ⇄ call_tools 循环）
- 与 Java 工作流框架（Camunda、Flowable）进行对比
- 学习时长：3 天
- 实践任务：手绘 Agent 图结构并跟踪一次请求的完整执行路径

---

## 1. Agent = LLM + 工具 + 决策循环

### 1.1 传统 RAG vs Agentic RAG

```
传统 RAG（固定流程）：
  用户提问 → 嵌入 → 向量检索 → 拼接上下文 → LLM 生成答案 → 返回

Agentic RAG（动态决策）：
  用户提问 → LLM 思考 → 需要查资料？→ 调用搜索工具
                         → 需要查统计？→ 调用统计工具
                         → 信息够了？→ 生成答案
                         → 信息还不够？→ 继续调用工具...
```

Agent 的关键能力：**自主决定**什么时候调用什么工具、调用多少次、什么时候结束。

### 1.2 ReAct 模式（Reasoning + Acting）

```
Reasoning（推理）  →  "我需要查一下知识库"
Acting（行动）     →  search_knowledge_base("什么是RAG")
Observation（观察）→  "找到了 5 条相关结果"
Reasoning（推理）  →  "信息够了，可以回答"
Acting（行动）     →  生成最终答案
```

这个循环在代码中体现为 **call_model → call_tools → call_model → call_tools → ... → END**。

---

## 2. LangGraph StateGraph 核心概念

### 2.1 State（状态）

状态是图中流转的"数据载体"。CaraBot 使用 `AgentState`：

```python
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    # add_messages 是 LangGraph 提供的 reducer：
    # - 新消息追加到列表末尾
    # - 相同 ID 的消息自动去重/合并
    # - ToolMessage 会更新对应的 AIMessage 的 tool_calls 状态
```

**状态是所有节点共享的**。每个节点读取 state，返回一个部分更新，LangGraph 自动合并。

### 2.2 Node（节点）

节点是图中的**处理单元**。CaraBot 有两个节点：

```python
# 节点 1：调用 LLM
async def call_model(state: AgentState, config: RunnableConfig) -> dict:
    messages = state["messages"]
    response = await self._model_with_tools.ainvoke(messages, config)
    return {"messages": [response]}  # 返回增量更新

# 节点 2：执行工具
async def call_tools(state: AgentState, config: RunnableConfig) -> dict:
    last_message = state["messages"][-1]
    tool_messages = []
    for tool_call in last_message.tool_calls:
        tool_fn = next((t for t in self._tools if t.name == tool_call["name"]), None)
        result = await tool_fn.ainvoke(tool_call["args"], config)
        tool_messages.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))
    return {"messages": tool_messages}
```

### 2.3 Edge（边）

边定义了节点之间的**流转规则**：

```python
# 普通边：call_tools 之后总是回到 call_model
workflow.add_edge("call_tools", "call_model")

# 条件边：call_model 之后根据结果决定去向
def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "call_tools"    # LLM 要调用工具 → 进入工具节点
    return END                 # LLM 给出了最终答案 → 结束

workflow.add_conditional_edges("call_model", should_continue, {
    "call_tools": "call_tools",
    END: END,
})
```

---

## 3. CaraBot 的 Agent 图结构

### 3.1 图的构建

```python
def _build_graph(self) -> CompiledStateGraph:
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("call_model", call_model)
    workflow.add_node("call_tools", call_tools)

    # 设置入口
    workflow.set_entry_point("call_model")

    # 添加条件边
    workflow.add_conditional_edges("call_model", should_continue, {
        "call_tools": "call_tools",
        END: END,
    })

    # 添加普通边
    workflow.add_edge("call_tools", "call_model")

    # 编译（绑定 Checkpointer 以持久化状态）
    return workflow.compile(checkpointer=self._checkpointer)
```

### 3.2 图的可视化表示

```
         ┌─────────────┐
         │  START      │
         └──────┬──────┘
                │
                ▼
         ┌─────────────┐
         │ call_model  │◄──────────────┐
         │ (LLM 推理)   │               │
         └──────┬──────┘               │
                │                      │
         工具调用？                     │
         ┌───┴───┐                    │
         │ YES   │ NO                  │
         ▼       ▼                    │
  ┌──────────┐  ┌─────┐              │
  │call_tools│  │ END │              │
  │(执行工具) │  └─────┘              │
  └────┬─────┘                        │
       │                              │
       └──────────────────────────────┘
```

### 3.3 一个完整对话的流转

```
用户："知识库里有几份文档？"

Step 1: call_model
  → LLM 收到 SystemMessage + HumanMessage("知识库里有几份文档？")
  → LLM 决策：需要调用 get_knowledge_base_stats 工具
  → 返回 AIMessage(tool_calls=[{name: "get_knowledge_base_stats", args: {}}])
  → should_continue: 有 tool_calls → "call_tools"

Step 2: call_tools
  → 执行 get_knowledge_base_stats()
  → 返回 ToolMessage(content="Knowledge Base Statistics:\n- Total: 42 docs\n...")
  → 自动回到 call_model

Step 3: call_model
  → LLM 收到 ToolMessage（工具结果）
  → LLM 决策：信息够了，生成答案
  → 返回 AIMessage(content="知识库里目前有 42 份文档。")
  → should_continue: 没有 tool_calls → END

总步数：call_model → call_tools → call_model → END
工具调用：1 次（get_knowledge_base_stats）
```

---

## 4. Checkpoint：对话状态持久化

### 4.1 为什么需要 Checkpoint？

Agent 对话可能跨多次 HTTP 请求。用户问"刚才那个问题再详细说说"，Agent 需要记得"刚才"指的是什么。

```python
# LangGraph Checkpoint 自动持久化每个节点执行后的状态
# 通过 thread_id 区分不同对话

# 第一次请求
POST /api/v1/chat {"message": "什么是RAG？"}
Response: {"thread_id": "abc-123", "message": "RAG是检索增强生成..."}

# 第二次请求（同一对话）
POST /api/v1/chat {"message": "它有什么优缺点？", "thread_id": "abc-123"}
# Agent 通过 thread_id 加载之前的状态，知道"它"指的是 RAG
```

### 4.2 实现

```python
async def startup(self):
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    checkpoint_url = self._settings.agent_checkpoint_db_url or (
        self._settings.db_url.replace("postgresql+asyncpg://", "postgresql://")
    )
    self._checkpointer = AsyncPostgresSaver.from_conn_string(checkpoint_url)
    await self._checkpointer.setup()  # 自动创建 checkpoints 表
    self._graph = self._build_graph()

async def run(self, message: str, thread_id=None):
    tid = thread_id or str(uuid.uuid4())
    config = {
        "configurable": {"thread_id": tid},
        "recursion_limit": self._settings.agent_max_iterations,  # 防止死循环
    }
    input_state = {
        "messages": [
            SystemMessage(content=self._settings.agent_system_prompt),
            HumanMessage(content=message),
        ],
    }
    result = await self._graph.ainvoke(input_state, config)
    # ...
```

### 4.3 recursion_limit：安全阀

```python
agent_max_iterations: int = Field(default=10, ge=1, le=50)
```

如果 LLM 在 call_model ⇄ call_tools 之间来回 10 次还没给出最终答案，LangGraph 会抛 `GraphRecursionError`，防止无限循环消耗 API 费用。

---

## 5. 与 Java 工作流框架对比

| 维度 | LangGraph | Camunda / Flowable |
|------|-----------|-------------------|
| 定位 | LLM Agent 编排 | 业务流程管理（BPMN） |
| 图定义 | Python 代码 | XML (BPMN 2.0) |
| 状态 | TypedDict（灵活） | 流程变量（强类型） |
| 条件分支 | Python 函数 | BPMN 网关（排他/并行/包容） |
| 持久化 | Checkpoint（PostgreSQL） | 流程实例（关系数据库） |
| 主要场景 | AI Agent 决策循环 | 审批流程、订单处理 |
| 学习曲线 | 低（纯 Python） | 高（BPMN 规范） |

**本质区别**：LangGraph 是为 LLM 的"不确定决策"设计的；Camunda 是为"确定规则"设计的。

---

## 6. 课后作业

1. **手绘 Agent 图**：画出 CaraBot Agent 的完整状态图（节点、边、条件），标注每个节点做了什么
2. **跟踪一次对话**：发送一条测试消息，在 AgentService 中加日志，跟踪 call_model → call_tools → call_model 的完整路径
3. **模拟 Checkpoint**：用 thread_id 做两次连续请求，验证第二次请求能"记住"第一次的上下文
4. **修改 System Prompt**：修改 `agent_system_prompt`，让 Agent 用中文回答，观察效果变化
5. **对比 BPMN**：用 Camunda Modeler 画一个等价的审批流程，感受 BPMN 和 StateGraph 的差异
6. **Agent 设计分析**：如果要把 CaraBot 从"单 Agent"升级为"多 Agent 协作"（一个负责检索、一个负责回答、一个负责校验），需要怎么修改 StateGraph？

---

## 📚 扩展阅读
- LangGraph 官方文档：https://langchain-ai.github.io/langgraph/
- ReAct 论文：https://arxiv.org/abs/2210.03629
- LangGraph Checkpoint 机制：https://langchain-ai.github.io/langgraph/concepts/persistence/
- Camunda BPMN：https://docs.camunda.org/manual/latest/reference/bpmn20/

---

**下节课预告**：第 21 课 - 工具定义与集成（LangChain Tool 装饰器、Pydantic args_schema、服务包装）

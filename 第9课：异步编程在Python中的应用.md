# CaraBot Agent 智能知识库系统课程
## 第 9 课：异步编程在 Python 中的应用

### 🎯 本节课目标
- 理解同步 vs 异步的本质区别：等待时能不能干别的事
- 掌握 `async/await` 语法及其在 CaraBot 中的实战用法
- 理解 `asyncio.to_thread`：怎么把同步代码包装成异步
- 学会用异步 SQLAlchemy 操作数据库
- 学习时长：2 天
- 实践任务：将同步代码改为异步

---

## 1. 为什么需要异步？

### 1.1 餐厅类比

**同步（一个服务员）**：
```
服务员 → 顾客 A 点菜 → 去厨房 → 等菜做好（干等 5 分钟）→ 上菜给 A
       → 顾客 B 点菜 → 去厨房 → 等菜做好（干等 5 分钟）→ 上菜给 B
       → 顾客 C 点菜 → ...
总耗时：15 分钟，大多数时间在干等
```

**异步（一个服务员）**：
```
服务员 → 顾客 A 点菜 → 去厨房下单（不等待，马上回来）
       → 顾客 B 点菜 → 去厨房下单（不等待，马上回来）
       → 顾客 C 点菜 → 去厨房下单（不等待，马上回来）
       → A 的菜好了 → 上菜给 A
       → B 的菜好了 → 上菜给 B
       → C 的菜好了 → 上菜给 C
总耗时：~5 分钟，等待时间被充分利用
```

### 1.2 Web 服务器的场景

```python
# ❌ 同步：一次只能处理一个请求
@app.get("/users")
def get_users():
    data = db.query("SELECT * FROM users")  # 等数据库 50ms
    result = requests.get("https://api.example.com/avatar")  # 等网络 200ms
    return process(data, result)  # 处理 10ms
# 总耗时 260ms，其中 250ms 在干等

# ✅ 异步：等待时处理其他请求
@app.get("/users")
async def get_users():
    data = await db.execute("SELECT * FROM users")   # 等待时去处理其他请求
    result = await http_client.get("https://...")     # 等待时又去处理其他请求
    return process(data, result)
# 等待期间服务器可以处理几十个其他请求
```

**关键认知**：异步不是让单个请求变快，而是让服务器在相同时间内处理更多请求。

---

## 2. async/await 基础

### 2.1 语法速查

```python
# 定义异步函数
async def fetch_data(url: str) -> dict:
    ...

# 调用异步函数（必须用 await）
data = await fetch_data("https://api.example.com")

# 定义异步上下文管理器
async with session.begin() as conn:
    ...

# 定义异步迭代器
async for chunk in stream:
    ...

# 并发执行多个异步任务
results = await asyncio.gather(
    fetch_data(url1),
    fetch_data(url2),
    fetch_data(url3),
)
```

### 2.2 核心规则（必背）

| 规则 | 说明 |
|------|------|
| `async def` 定义的函数叫协程 | 调用它不会立即执行，而是返回一个 coroutine 对象 |
| `await` 只能在 `async def` 内部使用 | 同步函数里不能用 await |
| `await` 后面必须是 awaitable 对象 | 协程、Task、Future 等 |
| 异步函数里才能调用异步函数 | 用 `await async_func()` |
| 同步函数里不能直接调用异步函数 | 需要用 `asyncio.run()` 或事件循环 |

---

## 3. CaraBot 中的异步实战

### 3.1 场景一：异步数据库操作

CaraBot 使用 SQLAlchemy 的异步扩展：

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# 创建异步引擎
engine = create_async_engine("postgresql+asyncpg://carabot:carabot@localhost:5432/carabot")

# 创建异步会话工厂
session_factory = async_sessionmaker(engine, expire_on_commit=False)

# 使用异步会话
async def check_duplicate(self, file_hash: str) -> DocumentRecord | None:
    async with self._session_factory() as session:          # async with
        result = await session.execute(                      # await
            select(DocumentRecord)
            .where(DocumentRecord.file_hash == file_hash)
            .where(DocumentRecord.status == "active")
        )
        return result.scalar_one_or_none()
```

**对比同步写法**：
```python
# 同步版
with Session() as session:
    result = session.execute(select(DocumentRecord).where(...))
    return result.scalar_one_or_none()

# 异步版（差异：async with + await）
async with session_factory() as session:
    result = await session.execute(select(DocumentRecord).where(...))
    return result.scalar_one_or_none()
```

### 3.2 场景二：同步代码异步化（asyncio.to_thread）

问题：BGE-m3 模型推理、Milvus SDK、PDF 解析库都是**同步**的，怎么在异步服务器中使用？

答案：`asyncio.to_thread()` —— 把同步函数丢到线程池里跑，不阻塞事件循环。

**EmbeddingService 中的用法**：
```python
class EmbeddingService:
    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        # self._model.encode() 是同步的（sentence-transformers 库）
        # 用 asyncio.to_thread 把它放到线程池
        embeddings = await asyncio.to_thread(
            self._model.encode,
            texts,
            batch_size=self._batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embeddings.tolist()
```

**DocumentProcessor 中的用法**：
```python
class DocumentProcessor:
    async def load_and_split(self, file_content, filename, mime_type=None):
        # LangChain 的 Loader 是同步的
        documents = await asyncio.to_thread(self._load_file, tmp_path, mime_type)
        chunks = await asyncio.to_thread(self._splitter.split_documents, documents)
        return chunks
```

**MilvusStore 中的用法**：
```python
class MilvusStore(BaseVectorStore):
    async def search(self, query_embedding, top_k=5, collection=None, threshold=None):
        def _search():
            col = self._get_collection(col_name)
            col.load()
            results = col.search(...)
            return results[0]

        hits = await asyncio.to_thread(_search)  # pymilvus 是同步的
        # ...
```

### 3.3 asyncio.to_thread 的原理

```
主事件循环（单线程）                线程池
─────────────────────        ─────────────────
await asyncio.to_thread()    →  在新线程中执行同步函数
事件循环继续处理其他请求          ← 函数执行完毕，返回结果
拿到结果，继续执行
```

**注意事项**：
- 线程池大小默认 `min(32, os.cpu_count() + 4)`
- 适合 I/O 密集型或 CPU 耗时不太长的操作
- 如果同步函数执行很久（10 秒+），会耗尽线程池

### 3.4 场景三：Agent 流式响应（async generator）

```python
class AgentService:
    async def stream(self, message: str, thread_id=None) -> AsyncIterator[dict]:
        # LangGraph 异步事件流
        async for event in self._graph.astream_events(input_state, config, version="v2"):
            kind = event["event"]
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield {"event": "token", "data": content}    # 流式吐出每个 token
            elif kind == "on_tool_start":
                yield {"event": "tool_call_start", "data": {...}}
            elif kind == "on_tool_end":
                yield {"event": "tool_call_end", "data": {...}}
        yield {"event": "done", "data": {"thread_id": tid}}
```

这个生成器让 ChatGPT 能"一个字一个字"地返回到前端，而不是等整段话写完了才发送。

### 3.5 场景四：启动时的并发健康检查

```python
async def lifespan(app: FastAPI):
    # 这些检查之间没有依赖关系，可以并发执行
    results = await asyncio.gather(
        check_database(session_factory),      # 检查 PostgreSQL
        check_vector_store(vector_store),     # 检查 Milvus/Chroma
        check_embedding_model(embedding_service),  # 检查 BGE-m3
        check_redis(settings.redis_url),      # 检查 Redis
        return_exceptions=True,               # 一个失败不影响其他
    )
    # asyncio.gather 并发执行，总耗时 ≈ 最慢的那个
```

---

## 4. 常见陷阱与最佳实践

### 4.1 陷阱一：在同步函数中调用异步函数

```python
# ❌ 错误
def sync_function():
    result = await async_function()  # SyntaxError: 'await' outside async function

# ✅ 正确
async def async_wrapper():
    result = await async_function()

# ✅ 或者在入口处用 asyncio.run()
def main():
    result = asyncio.run(async_function())
```

### 4.2 陷阱二：在异步函数里调用阻塞的同步函数

```python
# ❌ 错误：time.sleep 阻塞了整个事件循环
async def bad_example():
    time.sleep(5)  # 这 5 秒内，所有其他请求都被阻塞！
    return "done"

# ✅ 正确：用异步 sleep
async def good_example():
    await asyncio.sleep(5)  # 让出控制权，其他请求可以执行
    return "done"

# ✅ 正确：用 asyncio.to_thread 包装真正耗时的同步操作
async def also_good():
    result = await asyncio.to_thread(cpu_intensive_function, arg1, arg2)
    return result
```

### 4.3 陷阱三：忘记 await

```python
# ❌ 错误：忘记 await，coroutine 没有执行
async def bad():
    result = async_function()  # result 是一个 coroutine 对象，不是返回值！
    print(result)  # <coroutine object async_function at 0x...>

# ✅ 正确
async def good():
    result = await async_function()
    print(result)  # 实际的返回值
```

### 4.4 陷阱四：在 async with 里忘写 async

```python
# ❌ 错误
with session_factory() as session:   # AttributeError
    ...

# ✅ 正确
async with session_factory() as session:
    ...
```

---

## 5. 与 Java 异步编程的对比

| 维度 | Python (async/await) | Java (CompletableFuture / Virtual Threads) |
|------|---------------------|-------------------------------------------|
| 关键字 | `async def` + `await` | `CompletableFuture.supplyAsync()` |
| 模型 | 协程（单线程事件循环） | 线程池 / 虚拟线程（Project Loom） |
| 阻塞处理 | `asyncio.to_thread()` | `CompletableFuture.runAsync()` |
| 并发原语 | `asyncio.gather()` | `CompletableFuture.allOf()` |
| 学习曲线 | 中等（`await` 传染） | 较陡（Future 链式调用） |
| 性能 | 高（无线程切换开销） | 高（虚拟线程大幅减少开销） |

---

## 6. 实践：将同步代码改为异步

### 原始同步代码

```python
def process_document(file_path: str) -> dict:
    # 读取文件
    with open(file_path, "rb") as f:
        content = f.read()

    # 计算哈希
    file_hash = hashlib.sha256(content).hexdigest()

    # 查数据库
    session = Session()
    existing = session.execute(select(Document).where(Document.hash == file_hash)).first()

    if existing:
        return {"status": "duplicate", "id": existing.id}

    # 解析文档
    chunks = load_and_split(content)  # 同步耗时操作

    # 生成嵌入
    embeddings = model.encode([c.text for c in chunks])  # 同步耗时操作

    # 存向量库
    milvus.insert(embeddings)  # 同步耗时操作

    # 存数据库
    session.add(Document(hash=file_hash, chunks=len(chunks)))
    session.commit()

    return {"status": "success", "chunks": len(chunks)}
```

### 改写为异步版本

```python
async def process_document_async(file_path: str) -> dict:
    # 读取文件（用 aiofiles）
    import aiofiles
    async with aiofiles.open(file_path, "rb") as f:
        content = await f.read()

    # 计算哈希（CPU 操作，放到线程池）
    file_hash = await asyncio.to_thread(compute_hash, content)

    # 查数据库（异步 SQLAlchemy）
    async with async_session_factory() as session:
        result = await session.execute(
            select(Document).where(Document.hash == file_hash)
        )
        existing = result.first()

    if existing:
        return {"status": "duplicate", "id": existing.id}

    # 解析文档（同步库，放线程池）
    chunks = await asyncio.to_thread(load_and_split, content)

    # 生成嵌入（同步库，放线程池）
    embeddings = await asyncio.to_thread(
        model.encode, [c.text for c in chunks]
    )

    # 存向量库（同步 SDK，放线程池）
    await asyncio.to_thread(milvus.insert, embeddings)

    # 存数据库（异步 SQLAlchemy）
    async with async_session_factory() as session:
        session.add(Document(hash=file_hash, chunks=len(chunks)))
        await session.commit()

    return {"status": "success", "chunks": len(chunks)}
```

### 改写清单

| 同步写法 | 异步写法 |
|---------|---------|
| `def func():` | `async def func():` |
| `result = func()` | `result = await func()` |
| `with session:` | `async with session:` |
| `session.execute()` | `await session.execute()` |
| `session.commit()` | `await session.commit()` |
| `time.sleep(1)` | `await asyncio.sleep(1)` |
| `slow_sync_func()` | `await asyncio.to_thread(slow_sync_func)` |

---

## 7. 课后作业

1. **识别异步代码**：在 CaraBot 代码中找出所有 `async def`、`await`、`async with`、`asyncio.to_thread`，统计各有多少个
2. **改写练习**：将现有的同步文件处理函数改写为异步版本
3. **并发测试**：用 `asyncio.gather` 并发执行 5 个搜索请求，对比串行执行的时间
4. **性能分析**：在 `EmbeddingService.embed_documents` 中加时间打印，观察 `asyncio.to_thread` 的耗时占比
5. **对比练习**：用 Java 的 CompletableFuture 实现相同的并发搜索逻辑，对比代码量

---

## 📚 扩展阅读
- Python asyncio 官方文档：https://docs.python.org/3/library/asyncio.html
- SQLAlchemy 异步文档：https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- FastAPI 异步指南：https://fastapi.tiangolo.com/async/
- Real Python 异步教程：https://realpython.com/async-io-python/

---

**下节课预告**：第 10 课 - 数据模型与 ORM（SQLAlchemy 异步使用、DocumentRecord 模型设计、数据库迁移）

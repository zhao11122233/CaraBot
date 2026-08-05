# CaraBot Agent 智能知识库系统课程
## 第 10 课：数据模型与 ORM

### 🎯 本节课目标
- 理解 ORM（对象关系映射）的核心概念：用 Python 类操作数据库表
- 深入分析 CaraBot 的 DocumentRecord 模型设计
- 掌握 SQLAlchemy 2.0 异步 API 的实战用法
- 学习数据库索引设计和软删除模式
- 学习时长：2 天
- 实践任务：定义新的数据模型

---

## 1. ORM 是什么？

### 1.1 不用 ORM：手写 SQL

```python
# 原始 SQL
result = await conn.execute(
    "SELECT id, filename, file_hash FROM documents WHERE status = 'active' LIMIT 10"
)
rows = result.fetchall()
for row in rows:
    print(row[0], row[1], row[2])  # 通过索引访问，容易出错
```

**问题**：拼写错误要到运行时才发现、表结构改了要改几十处 SQL、没有类型安全。

### 1.2 用 ORM：操作 Python 对象

```python
# SQLAlchemy ORM
result = await session.execute(
    select(DocumentRecord).where(DocumentRecord.status == "active").limit(10)
)
records = result.scalars().all()
for record in records:
    print(record.id, record.filename, record.file_hash)  # 属性访问，IDE 有自动补全
```

**好处**：IDE 自动补全、编译时（类型）安全、不用手写 SQL、切换数据库（PostgreSQL → MySQL）只需改连接字符串。

---

## 2. CaraBot 的 DocumentRecord 模型

### 2.1 完整模型定义

```python
from uuid import uuid4
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Index, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from src.app.models import Base

class DocumentRecord(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    filename: Mapped[str] = mapped_column(
        String(512), nullable=False, comment="Original file name"
    )
    file_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True, comment="SHA256 hash"
    )
    file_size: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="File size in bytes"
    )
    author: Mapped[str | None] = mapped_column(
        String(256), nullable=True, comment="Document author"
    )
    mime_type: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="MIME type"
    )
    chunk_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="Number of text chunks"
    )
    collection_name: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="Vector store collection"
    )
    status: Mapped[str] = mapped_column(
        String(16), default="active", comment="active | deleted"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 复合索引
    __table_args__ = (
        Index("idx_documents_status", "status"),
        Index("idx_documents_filename_hash", "filename", "file_hash"),
    )
```

### 2.2 设计要点分析

| 设计决策 | 为什么这样做 |
|---------|------------|
| `UUID` 主键 | 分布式环境下唯一，不像自增 ID 那样有冲突风险 |
| `String(64)` for file_hash | SHA256 固定 64 个十六进制字符 |
| `String(512)` for filename | 足够容纳绝大多数文件名 |
| `status` 字段（软删除） | 不真删数据，标记为 deleted。方便恢复和审计 |
| `server_default=func.now()` | 由数据库生成时间戳，避免各服务器时钟不一致 |
| `onupdate=func.now()` | 每次更新自动刷新 `updated_at` |
| `index=True` on file_hash | 查重是高频操作，必须建索引 |
| 复合索引 `(filename, file_hash)` | 增量更新判断（同文件名+不同哈希）是常见查询 |

### 2.3 对应的数据库表结构

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    filename VARCHAR(512) NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    file_size INTEGER NOT NULL,
    author VARCHAR(256),
    mime_type VARCHAR(128) NOT NULL,
    chunk_count INTEGER DEFAULT 0,
    collection_name VARCHAR(128) NOT NULL,
    status VARCHAR(16) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_documents_file_hash ON documents (file_hash);
CREATE INDEX idx_documents_status ON documents (status);
CREATE INDEX idx_documents_filename_hash ON documents (filename, file_hash);
```

---

## 3. 异步 SQLAlchemy 实战

### 3.1 数据库引擎和会话的创建

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# 异步引擎
engine = create_async_engine(
    "postgresql+asyncpg://carabot:carabot@localhost:5432/carabot",
    echo=False,         # 不打印 SQL（生产环境）
    pool_size=5,        # 连接池大小
    max_overflow=10,    # 最大溢出连接数
)

# 异步会话工厂
session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False,  # 提交后不过期对象
)
```

### 3.2 CRUD 操作速查

```python
# === 查询（SELECT）===

# 按主键查
async with session_factory() as session:
    record = await session.get(DocumentRecord, doc_id)

# 按条件查一条
async with session_factory() as session:
    result = await session.execute(
        select(DocumentRecord)
        .where(DocumentRecord.file_hash == hash_value)
        .where(DocumentRecord.status == "active")
        .limit(1)
    )
    record = result.scalar_one_or_none()  # 有则返回，无则 None

# 按条件查多条
async with session_factory() as session:
    result = await session.execute(
        select(DocumentRecord)
        .where(DocumentRecord.status == "active")
        .order_by(DocumentRecord.created_at.desc())
        .limit(10)
    )
    records = result.scalars().all()

# 聚合查询
async with session_factory() as session:
    result = await session.execute(
        select(DocumentRecord).where(DocumentRecord.status == "active")
    )
    total_chunks = sum(r.chunk_count for r in result.scalars().all())

# === 插入（INSERT）===
async with session_factory() as session:
    record = DocumentRecord(
        filename="test.pdf",
        file_hash="abc123...",
        file_size=102400,
        mime_type="application/pdf",
        chunk_count=15,
        collection_name="carabot_knowledge",
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)  # 刷新以获取数据库生成的默认值

# === 更新（UPDATE）===
async with session_factory() as session:
    await session.execute(
        update(DocumentRecord)
        .where(DocumentRecord.id == doc_id)
        .values(status="deleted", updated_at=datetime.now(timezone.utc))
    )
    await session.commit()

# === 删除（物理删除，CaraBot 不使用）===
async with session_factory() as session:
    record = await session.get(DocumentRecord, doc_id)
    await session.delete(record)
    await session.commit()
```

### 3.3 关键 API 速查

| API | 用途 | 返回值 |
|-----|------|--------|
| `session.get(Model, id)` | 按主键查询 | Model 实例或 None |
| `session.execute(select(...))` | 执行查询 | Result 对象 |
| `result.scalar_one_or_none()` | 取单个结果 | Model 实例或 None |
| `result.scalars().all()` | 取所有结果 | list[Model] |
| `session.add(obj)` | 添加对象 | None |
| `await session.commit()` | 提交事务 | None |
| `await session.refresh(obj)` | 刷新对象 | None |

---

## 4. 数据库初始化与引擎创建

### 4.1 create_engine_and_session

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """所有 ORM 模型的基类"""
    pass

def create_engine_and_session(settings: Settings):
    """创建异步数据库引擎和会话工厂"""
    engine = create_async_engine(
        settings.db_url,
        echo=(settings.log_level == "DEBUG"),
        pool_size=5,
        max_overflow=10,
    )
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False,
    )
    return engine, session_factory
```

### 4.2 启动时自动建表

在 `create_app()` 的 lifespan 中：

```python
from src.app.models import Base

async with db_engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
    # create_all 是同步的，用 run_sync 包一下
```

**注意**：`Base.metadata.create_all` 只创建不存在的表，不会修改已存在的表结构。真正的数据库迁移（migration）需要用 Alembic。

---

## 5. 软删除模式

### 5.1 什么是软删除？

不真的删除数据，而是标记 `status = "deleted"`。

```python
# CaraBot 的增量更新流程
async def upload(self, file_content, filename, ...):
    file_hash = compute_hash(content)

    # 查是否重复
    existing = await dedup_service.check_duplicate(file_hash)
    if existing:
        return {"is_duplicate": True, "document_id": existing.id}

    # 查是否有旧版本
    old_record = await dedup_service.find_by_filename(filename)
    if old_record:
        # 软删除旧版本（不真删！）
        await vector_store.delete([old_record.id], collection)
        await dedup_service.mark_deleted(old_record.id)
        # 继续处理新版本...

    # 插入新记录
    await dedup_service.register_document(...)
```

### 5.2 mark_deleted 实现

```python
async def mark_deleted(self, doc_id: str) -> None:
    uid = UUID(doc_id)
    async with self._session_factory() as session:
        await session.execute(
            update(DocumentRecord)
            .where(DocumentRecord.id == uid)
            .values(status="deleted", updated_at=datetime.now(timezone.utc))
        )
        await session.commit()
```

### 5.3 查询总是过滤 status

```python
# 所有业务查询都加上 status == "active"
result = await session.execute(
    select(DocumentRecord)
    .where(DocumentRecord.file_hash == hash_value)
    .where(DocumentRecord.status == "active")  # ← 必须加这个条件
    .limit(1)
)
```

---

## 6. 实践：添加 ChatHistory 模型

### 需求

新增一个对话历史表，记录每次 Agent 对话。

### 模型设计

```python
class ChatHistory(Base):
    __tablename__ = "chat_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    thread_id: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True, comment="Conversation thread ID"
    )
    role: Mapped[str] = mapped_column(
        String(16), nullable=False, comment="user | assistant | system | tool"
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Message content"
    )
    tool_name: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="Tool name if role=tool"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("idx_chat_thread", "thread_id", "created_at"),
    )
```

### 使用示例

```python
# 记录用户消息
async with session_factory() as session:
    session.add(ChatHistory(
        thread_id="thread-123",
        role="user",
        content="什么是RAG？",
    ))
    await session.commit()

# 查询对话历史
async with session_factory() as session:
    result = await session.execute(
        select(ChatHistory)
        .where(ChatHistory.thread_id == "thread-123")
        .order_by(ChatHistory.created_at)
    )
    messages = result.scalars().all()
```

---

## 7. 课后作业

1. **分析 DocumentRecord**：列出所有字段及其类型，解释为什么每个字段的类型和长度是这样设计的
2. **写 SQL**：为以下查询手写等价的 SQL 语句：
   - 按 file_hash 查一条 active 记录
   - 统计所有 active 文档的总 chunk_count
   - 查最近 7 天创建的文档
3. **设计新模型**：为 CaraBot 设计一个 `ApiKey` 表（支持多个 API Key、每个有不同权限、可以设置过期时间）
4. **对比 JPA**：用 Java JPA 注解写一个等价的 DocumentRecord，对比 SQLAlchemy 和 JPA 的写法差异
5. **索引分析**：分析 DocumentRecord 上的所有索引，解释每个索引分别加速了哪个业务查询

---

## 📚 扩展阅读
- SQLAlchemy 2.0 文档：https://docs.sqlalchemy.org/en/20/
- SQLAlchemy 异步指南：https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- PostgreSQL UUID 类型：https://www.postgresql.org/docs/current/datatype-uuid.html

---

**下节课预告**：第 11 课 - 日志系统与监控（结构化 JSON 日志、trace_id 分布式追踪、健康检查）

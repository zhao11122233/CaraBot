# CaraBot Agent 智能知识库系统课程
## 第 17 课：Milvus 向量存储（生产环境）

### 🎯 本节课目标
- 理解 Milvus 的分布式架构（Proxy、Data Node、Index Node、Meta Store）
- 掌握 pymilvus 的 Collection、Schema、Index、Search API
- 深入分析 CaraBot 的 MilvusStore 完整实现
- 学会将同步 Milvus SDK 包装为异步操作
- 学习时长：2 天
- 实践任务：部署 Milvus 并测试

---

## 1. Milvus 架构概览

### 1.1 核心组件

```
┌────────────────────────────────────────────┐
│                  客户端 SDK                  │
│              (pymilvus)                     │
└──────────────────┬─────────────────────────┘
                   │ gRPC
┌──────────────────▼─────────────────────────┐
│              Proxy（代理）                    │
│         请求路由、负载均衡、限流                │
└──────┬──────────────┬──────────────────────┘
       │              │
┌──────▼──────┐ ┌─────▼───────┐
│  Data Node  │ │ Index Node  │  ← 计算层
│  数据写入    │ │  索引构建    │
└──────┬──────┘ └─────┬───────┘
       │              │
┌──────▼──────────────▼───────┐
│     Meta Store (etcd)       │  ← 元数据
│     Object Store (MinIO/S3) │  ← 持久化存储
└─────────────────────────────┘
```

### 1.2 关键概念

| 概念 | 说明 | 类比 |
|------|------|------|
| **Collection** | 向量集合 | PostgreSQL 的表 |
| **Partition** | 集合的分区 | PostgreSQL 的表分区 |
| **FieldSchema** | 字段定义 | 列定义 |
| **Index** | 向量索引（FLAT/IVF/HNSW） | B-Tree 索引 |
| **Segment** | 数据的最小存储单元 | PostgreSQL 的 Page |

---

## 2. CaraBot 的 MilvusStore 实现

### 2.1 连接管理

```python
class MilvusStore(BaseVectorStore):
    def __init__(self, settings: Settings):
        self._host = settings.milvus_host
        self._port = settings.milvus_port
        self._user = settings.milvus_user
        self._password = settings.milvus_password
        self._default_collection = settings.milvus_collection_name
        self._dimension = settings.milvus_dimension
        self._connected = False  # 懒连接

    async def _ensure_connected(self):
        if self._connected:
            return

        def _connect():
            connections.connect(
                alias="default",
                host=self._host, port=self._port,
                user=self._user, password=self._password,
            )

        await asyncio.to_thread(_connect)  # pymilvus 是同步的
        self._client = MilvusClient(uri=f"http://{self._host}:{self._port}")
        self._connected = True
```

### 2.2 集合创建

```python
def _create_collection(self, collection_name: str) -> Collection:
    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=128, is_primary=True),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self._dimension),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
        FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=128),
        FieldSchema(name="metadata", dtype=DataType.JSON),
    ]
    schema = CollectionSchema(fields, description="CaraBot knowledge base")
    collection = Collection(collection_name, schema=schema)

    # FLAT 索引：精确搜索（Brute Force），适合中小规模
    index_params = {
        "metric_type": "IP",       # 内积（等价于归一化后的余弦相似度）
        "index_type": "FLAT",
        "params": {},
    }
    collection.create_index("embedding", index_params)
    collection.load()  # 加载到内存
    return collection
```

### 2.3 文档入库

```python
async def add_documents(self, documents, collection=None, embeddings=None):
    await self._ensure_connected()
    col_name = collection or self._default_collection

    chunk_ids, data_rows = [], []
    for i, doc in enumerate(documents):
        chunk_id = str(uuid.uuid4())
        chunk_ids.append(chunk_id)
        data_rows.append({
            "id": chunk_id,
            "embedding": embeddings[i] if embeddings else [],
            "text": doc.page_content,
            "doc_id": doc.metadata.get("document_id", ""),
            "metadata": doc.metadata,
        })

    def _insert():
        col = self._get_collection(col_name)
        col.insert(data_rows)
        col.flush()  # 持久化到磁盘

    await asyncio.to_thread(_insert)
    return chunk_ids
```

### 2.4 语义搜索

```python
async def search(self, query_embedding, top_k=5, collection=None, threshold=None):
    await self._ensure_connected()
    col_name = collection or self._default_collection

    def _search():
        col = self._get_collection(col_name)
        col.load()
        search_params = {"metric_type": "IP", "params": {"nprobe": 16}}
        results = col.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["text", "doc_id", "metadata"],
        )
        return results[0]

    hits = await asyncio.to_thread(_search)

    results = []
    for hit in hits:
        score = float(hit.score)
        if threshold is not None and score < threshold:
            continue
        doc = Document(
            page_content=hit.entity.get("text", ""),
            metadata={
                "chunk_id": hit.id,
                "document_id": hit.entity.get("doc_id", ""),
                **hit.entity.get("metadata", {}),
            },
        )
        results.append((doc, score))
    return results
```

### 2.5 删除

```python
async def delete(self, doc_ids, collection=None):
    await self._ensure_connected()
    col_name = collection or self._default_collection

    def _delete():
        col = self._get_collection(col_name)
        expr = f"doc_id in {json.dumps(doc_ids)}"  # 标量过滤
        result = col.delete(expr)
        col.flush()
        return result.delete_count if result else 0

    import json
    count = await asyncio.to_thread(_delete)
    return count
```

---

## 3. FLAT vs HNSW 索引选择

CaraBot 默认使用 FLAT（暴力搜索），适合数据量 < 10 万的场景。如果扩展到百万级：

```python
# 切换到 HNSW 索引（更高性能）
index_params = {
    "metric_type": "IP",
    "index_type": "HNSW",
    "params": {
        "M": 16,           # 每个节点的连接数（越大精度越高，内存越大）
        "efConstruction": 200,  # 构建时搜索宽度
    },
}

# 搜索参数
search_params = {
    "metric_type": "IP",
    "params": {"ef": 64},  # 搜索时宽度（越大精度越高，速度越慢）
}
```

---

## 4. 同步 SDK 异步化的模式

CaraBot 大量使用这个模式来包装 pymilvus：

```python
# 模式模板
async def async_operation(self, ...):
    await self._ensure_connected()

    def _sync_work():
        # pymilvus 的同步操作
        col = self._get_collection(col_name)
        result = col.some_operation(...)
        return result

    return await asyncio.to_thread(_sync_work)
```

**关键点**：
- 把同步操作封装在一个内部函数中
- 通过 `asyncio.to_thread()` 发送到线程池
- 不阻塞主事件循环

---

## 5. 课后作业

1. **部署 Milvus**：用 Docker Compose 启动 Milvus Standalone
2. **对比索引**：在相同 5 万条数据上，对比 FLAT、IVF_FLAT、HNSW 三种索引的 QPS 和 Recall
3. **搜索参数调优**：调整 `nprobe`（IVF）或 `ef`（HNSW），绘制 QPS vs Recall 曲线
4. **分区实践**：按文档语言创建 Milvus Partition，验证分区搜索的性能提升
5. **CaraBot 切换**：将 CaraBot 的 VECTOR_STORE_TYPE 从 chroma 切换到 milvus，验证功能一致性

---

## 📚 扩展阅读
- Milvus 官方文档：https://milvus.io/docs
- pymilvus API：https://milvus.io/api-reference/pymilvus/v2.4.x/About.md
- HNSW 论文：https://arxiv.org/abs/1603.09320

---

**下节课预告**：第 18 课 - 相似性搜索优化

# CaraBot Agent 智能知识库系统课程
## 第 16 课：Chroma 向量存储（开发环境）

### 🎯 本节课目标
- 掌握 Chroma 的本地部署和使用
- 深入分析 CaraBot 的 ChromaStore 实现
- 理解 Chroma 的距离度量与相似度转换
- 学习时长：1 天
- 实践任务：使用 Chroma 进行向量操作

---

## 1. Chroma 快速入门

### 1.1 什么是 Chroma？

Chroma 是一个开源的**嵌入式向量数据库**，专为开发环境和小规模应用设计。它跑在你的 Python 进程里，数据存为本地文件，零配置。

### 1.2 5 分钟上手

```bash
pip install chromadb
```

```python
import chromadb

# 创建客户端（数据存在 ./data/chroma/）
client = chromadb.PersistentClient(path="./data/chroma")

# 创建集合
collection = client.create_collection(
    name="my_knowledge",
    metadata={"hnsw:space": "cosine"},  # 使用余弦相似度
)

# 存入文档
collection.add(
    documents=["RAG是检索增强生成的缩写", "向量数据库用于存储和检索向量"],
    metadatas=[{"source": "doc1"}, {"source": "doc2"}],
    ids=["id1", "id2"],
)

# 查询
results = collection.query(
    query_texts=["什么是RAG？"],  # Chroma 可以自动嵌入！
    n_results=2,
)
print(results["documents"])  # [["RAG是检索增强生成的缩写", ...]]
```

---

## 2. CaraBot 的 ChromaStore 实现

### 2.1 初始化

```python
class ChromaStore(BaseVectorStore):
    def __init__(self, settings: Settings):
        self._persist_dir = settings.chroma_persist_dir     # "./data/chroma"
        self._default_collection = settings.chroma_collection_name  # "carabot_knowledge"
        self._dimension = settings.milvus_dimension          # 1024
        self._client = None  # 懒加载

    def _get_client(self) -> chromadb.PersistentClient:
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=self._persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        return self._client
```

### 2.2 集合管理

```python
def _get_or_create_collection(self, collection_name: str):
    client = self._get_client()
    try:
        return client.get_collection(collection_name)
    except Exception:
        # 集合不存在，创建新的
        return client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},  # 余弦距离
        )
```

### 2.3 文档入库

```python
async def add_documents(self, documents, collection=None, embeddings=None):
    col_name = collection or self._default_collection
    col = self._get_or_create_collection(col_name)

    chunk_ids, texts, metadatas = [], [], []
    for doc in documents:
        cid = str(uuid.uuid4())
        chunk_ids.append(cid)
        texts.append(doc.page_content)
        metadatas.append({**doc.metadata, "chunk_id": cid})

    col.add(
        documents=texts,
        metadatas=metadatas,
        ids=chunk_ids,
        embeddings=embeddings,  # CaraBot 预生成嵌入，不依赖 Chroma 自动嵌入
    )
    return chunk_ids
```

### 2.4 语义搜索

```python
async def search(self, query_embedding, top_k=5, collection=None, threshold=None):
    col_name = collection or self._default_collection
    col = self._get_or_create_collection(col_name)

    results = col.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    output = []
    for i, doc_id in enumerate(results["ids"][0]):
        distance = results["distances"][0][i]

        # Chroma 返回的是余弦距离，需转换为相似度
        # 余弦距离 ∈ [0, 2]，余弦相似度 = 1 - 距离/2
        score = 1.0 - (distance / 2.0)

        if threshold is not None and score < threshold:
            continue

        doc = Document(
            page_content=results["documents"][0][i] or "",
            metadata=results["metadatas"][0][i] or {},
        )
        output.append((doc, score))

    return output
```

### 2.5 距离 vs 相似度转换

Chroma 的 `hnsw:space:cosine` 返回的是**余弦距离**，不是余弦相似度：

```
余弦相似度 ∈ [-1, 1]    1 = 完全相同，0 = 无关，-1 = 完全相反
余弦距离 ∈ [0, 2]       0 = 完全相同，1 = 无关，2 = 完全相反

转换公式：相似度 = 1 - 距离/2

验证：
  距离 = 0（完全相同）  → 相似度 = 1 - 0/2 = 1.0  ✅
  距离 = 1（无关）      → 相似度 = 1 - 1/2 = 0.5  ✅
  距离 = 2（完全相反）  → 相似度 = 1 - 2/2 = 0.0  ✅
```

### 2.6 删除

```python
async def delete(self, doc_ids, collection=None):
    col = self._get_or_create_collection(collection or self._default_collection)

    # Chroma 不支持按 doc_id 删除，先查所有 ID 再过滤
    all_ids = col.get()["ids"]
    to_delete = [did for did in doc_ids if did in all_ids]
    if to_delete:
        col.delete(ids=to_delete)
    return len(to_delete)
```

---

## 3. Chroma vs Milvus 操作对比

| 操作 | Chroma | Milvus |
|------|--------|--------|
| 连接 | `PersistentClient(path="./data")` | `connections.connect(host=..., port=...)` |
| 创建集合 | `client.create_collection(name)` | `Collection(name, schema)` |
| 插入 | `col.add(documents=..., ids=..., embeddings=...)` | `col.insert([{...}])` + `col.flush()` |
| 搜索 | `col.query(query_embeddings=..., n_results=5)` | `col.search(data=..., anns_field=..., param=..., limit=5)` |
| 删除 | `col.delete(ids=[...])` | `col.delete(expr="doc_id in [...]")` |
| 持久化 | 自动存文件 | 需手动 `flush()` |
| 相似度 | 返回距离，需转换 | 直接返回 score |

---

## 4. Chroma 的适用场景与限制

| 方面 | 评价 |
|------|------|
| 开发环境 | ✅ 完美，零配置 |
| 小规模生产（<10万文档） | ✅ 可用 |
| 大规模生产（百万+文档） | ❌ 性能不足 |
| 分布式/高可用 | ❌ 不支持 |
| 数据备份 | ⚠️ 拷贝文件目录即可 |
| Python API 友好度 | ✅ 非常好 |

---

## 5. 课后作业

1. **启动 Chroma**：本地运行 `chromadb.PersistentClient`，创建一个集合，存入 10 条模拟数据，执行查询
2. **对比转换公式**：分别用 Chroma 原生 `query_texts`（自动嵌入）和手动嵌入后 `query`，对比结果一致性
3. **持久化验证**：重启 Python 进程，重新连接同一个 `persist_dir`，验证数据是否仍然存在
4. **性能测试**：分别存入 1000、10000、50000 条数据，记录查询耗时变化
5. **代码阅读**：对比 `ChromaStore.add_documents` 和 `MilvusStore.add_documents`，写出 5 个实现差异

---

## 📚 扩展阅读
- Chroma 官方文档：https://docs.trychroma.com/
- Chroma GitHub：https://github.com/chroma-core/chroma

---

**下节课预告**：第 17 课 - Milvus 向量存储（生产环境）

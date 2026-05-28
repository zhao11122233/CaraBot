# CaraBot

企业级多语言 RAG 知识检索模块 —— 复现传音 Carlcare AICC 核心能力。

## 功能特性

- **多格式文档摄入**：支持 PDF、DOCX、Markdown、TXT
- **多语言嵌入**：BGE-m3 模型，支持中文、英文、斯瓦希里语
- **双向量存储**：Milvus（生产环境）/ Chroma（开发环境），通过配置切换
- **文档去重**：基于 SHA256 哈希的去重机制，支持增量更新
- **API Key 鉴权**：所有接口通过 `X-API-Key` 请求头进行认证
- **结构化 JSON 日志**：每个请求带 trace_id，便于分布式追踪
- **健康检查**：组件级监控（数据库、向量存储、模型、Redis）
- **Recall@k 评估**：内置评估工具，支持按语言分析 badcase

## 快速开始

### 环境要求

- Python 3.10+
- Docker 和 Docker Compose（用于基础设施）

### 1. 克隆并配置

```bash
git clone <repo-url>
cd CaraBot

# 复制并编辑环境变量文件
cp .env.example .env
# 编辑 .env —— 至少需要将 API_KEY 修改为安全的值
```

### 2. 启动基础设施

```bash
docker-compose up -d postgres redis milvus-standalone etcd minio
```

### 3. 初始化数据库

```bash
pip install -r requirements.txt
python scripts/init_db.py
```

### 4. 启动应用

```bash
uvicorn src.app.main:create_app --factory --host 0.0.0.0 --port 8000 --reload
```

### 5. 验证

```bash
curl http://localhost:8000/health
```

## API 文档

所有 `/api/v1/*` 接口均需携带 `X-API-Key` 请求头。`/health` 接口无需认证。

### POST /api/v1/upload

上传并索引文档。

```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -H "X-API-Key: your-api-key" \
  -F "file=@document.pdf" \
  -F "author=John Doe" \
  -F "collection=faq"
```

**响应示例：**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "document.pdf",
  "file_hash": "abc123...",
  "file_size": 102400,
  "chunk_count": 15,
  "is_duplicate": false,
  "message": "Document processed successfully."
}
```

### POST /api/v1/search

搜索知识库。

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "如何重置密码？", "top_k": 5, "threshold": 0.7}'
```

**响应示例：**
```json
{
  "query": "如何重置密码？",
  "total_results": 3,
  "results": [
    {
      "document_id": "550e8400-...",
      "content": "要重置密码，请前往设置页面...",
      "score": 0.8921,
      "metadata": {"filename": "user_guide.pdf", "author": "Support Team"}
    }
  ],
  "search_time_ms": 45.32
}
```

### GET /api/v1/stats

获取知识库统计信息。

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v1/stats
```

### GET /health

健康检查 —— 无需认证。

```bash
curl http://localhost:8000/health
```

**响应示例：**
```json
{
  "status": "up",
  "checks": {
    "db": {"status": "up", "detail": null},
    "vector_store": {"status": "up", "detail": null},
    "model": {"status": "up", "detail": null},
    "redis": {"status": "up", "detail": null}
  }
}
```

## 环境变量

完整配置项参见 [.env.example](.env.example)。

| 变量 | 是否必填 | 默认值 | 说明 |
|---|---|---|---|
| `API_KEY` | **是** | — | API 请求认证密钥 |
| `VECTOR_STORE_TYPE` | 否 | `milvus` | 向量存储类型：`milvus` 或 `chroma` |
| `MILVUS_HOST` | Milvus 时必填 | `localhost` | Milvus 服务器主机名 |
| `MILVUS_PORT` | 否 | `19530` | Milvus 服务器端口 |
| `DB_URL` | **是** | — | PostgreSQL 连接字符串（asyncpg） |
| `REDIS_URL` | 否 | `redis://localhost:6379/0` | Redis 连接字符串 |
| `BGE_MODEL_PATH` | 否 | `./data/models/bge-m3` | 本地模型缓存目录 |
| `BGE_MODEL_NAME` | 否 | `BAAI/bge-m3` | HuggingFace 模型标识符 |
| `CHUNK_SIZE` | 否 | `500` | 文本分块大小 |
| `CHUNK_OVERLAP` | 否 | `50` | 分块重叠大小 |
| `TOP_K` | 否 | `5` | 默认搜索结果数量 |
| `SIMILARITY_THRESHOLD` | 否 | `0.7` | 最低相似度阈值 |
| `LOG_LEVEL` | 否 | `INFO` | 日志级别 |
| `LOG_FILE` | 否 | `./logs/carabot.log` | 日志文件路径 |
| `LOG_FORMAT` | 否 | `json` | 日志格式：`json` 或 `text` |

## 运行测试

```bash
pytest tests/ -v

# 带覆盖率报告
pytest tests/ -v --cov=src/app --cov-report=term-missing
```

## 部署

### Docker Compose（完整技术栈）

```bash
# 构建并启动所有服务
docker-compose up -d --build
```

### 生产环境注意事项

1. 设置强密码 `API_KEY` —— 至少 32 位随机字符
2. 使用独立的 Milvus 集群以保证高可用性
3. 配置 PostgreSQL 主从复制
4. 使用反向代理（nginx/Caddy）进行 TLS 终止
5. 设置 `LOG_FORMAT=json` 以便接入 ELK/Loki
6. 根据 CPU 核数调整 `WORKERS`（通常为 `2 * CPU 核数 + 1`）

## 项目结构

```
cara-bot/
├── src/app/
│   ├── api/              # API 路由和中间件
│   │   ├── routes/       # upload、search、stats、health
│   │   └── __init__.py   # 路由注册
│   ├── core/             # 配置、日志、异常
│   ├── models/           # SQLAlchemy ORM、Pydantic schema
│   ├── services/         # 业务逻辑
│   ├── vectorstore/      # 向量存储抽象层（Milvus/Chroma）
│   ├── middleware/        # 认证、日志、错误处理
│   └── main.py           # 应用工厂
├── tests/                # 单元测试
├── scripts/              # init_db、evaluate 脚本
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── README.md
└── README_zh.md
```

## 许可证

内部使用。
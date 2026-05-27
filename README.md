# CaraBot

Enterprise multi-language RAG knowledge retrieval module — replicating the core capabilities of Transsion Carlcare AICC.

## Features

- **Multi-format document ingestion**: PDF, DOCX, Markdown, TXT
- **Multi-language embeddings**: BGE-m3 supporting Chinese, English, Swahili
- **Dual vector store**: Milvus (production) / Chroma (development) — switchable via config
- **Document deduplication**: SHA256 hash-based with incremental update support
- **API Key authentication**: All endpoints protected via `X-API-Key` header
- **Structured JSON logging**: Per-request trace_id for distributed tracing
- **Health checks**: Component-level monitoring (DB, vector store, model, Redis)
- **Recall@k evaluation**: Built-in evaluation with per-language badcase analysis

## Quick Start

### Prerequisites

- Python 3.10+
- Docker & Docker Compose (for infrastructure)

### 1. Clone and configure

```bash
git clone <repo-url>
cd CaraBot

# Copy and edit the environment file
cp .env.example .env
# Edit .env — at minimum change API_KEY to a secure value
```

### 2. Start infrastructure

```bash
docker-compose up -d postgres redis milvus-standalone etcd minio
```

### 3. Initialize the database

```bash
pip install -r requirements.txt
python scripts/init_db.py
```

### 4. Start the application

```bash
uvicorn src.app.main:create_app --factory --host 0.0.0.0 --port 8000 --reload
```

### 5. Verify

```bash
curl http://localhost:8000/health
```

## API Documentation

All `/api/v1/*` endpoints require `X-API-Key` header. The `/health` endpoint is public.

### POST /api/v1/upload

Upload and index a document.

```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -H "X-API-Key: your-api-key" \
  -F "file=@document.pdf" \
  -F "author=John Doe" \
  -F "collection=faq"
```

**Response:**
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

Search the knowledge base.

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "How to reset password?", "top_k": 5, "threshold": 0.7}'
```

**Response:**
```json
{
  "query": "How to reset password?",
  "total_results": 3,
  "results": [
    {
      "document_id": "550e8400-...",
      "content": "To reset your password, go to Settings...",
      "score": 0.8921,
      "metadata": {"filename": "user_guide.pdf", "author": "Support Team"}
    }
  ],
  "search_time_ms": 45.32
}
```

### GET /api/v1/stats

Get knowledge base statistics.

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v1/stats
```

### GET /health

Health check — no auth required.

```bash
curl http://localhost:8000/health
```

**Response:**
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

## Environment Variables

See [.env.example](.env.example) for all configuration options.

| Variable | Required | Default | Description |
|---|---|---|---|
| `API_KEY` | **Yes** | — | API key for request authentication |
| `VECTOR_STORE_TYPE` | No | `milvus` | `milvus` or `chroma` |
| `MILVUS_HOST` | If Milvus | `localhost` | Milvus server hostname |
| `MILVUS_PORT` | No | `19530` | Milvus server port |
| `DB_URL` | **Yes** | — | PostgreSQL connection string (asyncpg) |
| `REDIS_URL` | No | `redis://localhost:6379/0` | Redis connection string |
| `BGE_MODEL_PATH` | No | `./data/models/bge-m3` | Local model cache directory |
| `BGE_MODEL_NAME` | No | `BAAI/bge-m3` | HuggingFace model identifier |
| `CHUNK_SIZE` | No | `500` | Text chunk size |
| `CHUNK_OVERLAP` | No | `50` | Chunk overlap |
| `TOP_K` | No | `5` | Default search result count |
| `SIMILARITY_THRESHOLD` | No | `0.7` | Minimum similarity score |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `LOG_FILE` | No | `./logs/carabot.log` | Log file path |
| `LOG_FORMAT` | No | `json` | `json` or `text` |

## Running Tests

```bash
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=src/app --cov-report=term-missing
```

## Deployment

### Docker Compose (full stack)

```bash
# Build and start all services
docker-compose up -d --build
```

### Production considerations

1. Set a strong `API_KEY` — at least 32 random characters
2. Use a dedicated Milvus cluster for high availability
3. Configure PostgreSQL with replication
4. Use a reverse proxy (nginx/Caddy) for TLS termination
5. Set `LOG_FORMAT=json` for ELK/Loki ingestion
6. Increase `WORKERS` based on CPU cores (typically `2 * cores + 1`)

## Project Structure

```
cara-bot/
├── src/app/
│   ├── api/              # API routes and middleware
│   │   ├── routes/       # upload, search, stats, health
│   │   └── __init__.py   # Router registration
│   ├── core/             # Config, logging, exceptions
│   ├── models/           # SQLAlchemy ORM, Pydantic schemas
│   ├── services/         # Business logic
│   ├── vectorstore/      # Vector store abstraction (Milvus/Chroma)
│   ├── middleware/        # Auth, logging, error handling
│   └── main.py           # Application factory
├── tests/                # Unit tests
├── scripts/              # init_db, evaluate
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

## License

Internal use.

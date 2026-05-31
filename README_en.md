# CaraBot: Agent-Powered Intelligent Knowledge Base System

[![GitHub Stars](https://img.shields.io/github/stars/zhao11122233/CaraBot?style=flat-square)](https://github.com/zhao11122233/CaraBot)
[![GitHub Issues](https://img.shields.io/github/issues/zhao11122233/CaraBot?style=flat-square)](https://github.com/zhao11122233/CaraBot/issues)
[![GitHub License](https://img.shields.io/github/license/zhao11122233/CaraBot?style=flat-square)](https://github.com/zhao11122233/CaraBot/blob/main/LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.10+-blue?style=flat-square)](https://python.org)

---

### [🌐 中文版本](README.md)

## 📖 Overview

CaraBot is an Agent-powered intelligent knowledge base system built on LangGraph and RAG (Retrieval-Augmented Generation) architecture. It combines semantic search with LLM-driven conversational AI, enabling natural language interaction with your document corpus. The built-in ReAct agent can autonomously search, retrieve, and ingest documents to answer user queries accurately and efficiently.

### ✨ Key Advantages

- 🚀 **High Performance**: Based on FastAPI and Milvus vector database, supporting high-concurrency retrieval
- 🤖 **Agent-Powered**: LangGraph ReAct agent with tool-calling for autonomous knowledge base interaction
- 💬 **Conversational AI**: Multi-turn dialogue with streaming SSE responses via OpenAI-compatible LLMs
- 🌐 **Multi-language Support**: Supports Chinese, English, Swahili, and other languages
- 📚 **Multi-format Support**: Supports PDF, DOCX, Markdown, TXT, and other common document formats
- 🔒 **Enterprise-grade Security**: Provides API Key authentication, data encryption, and other security features
- 📊 **Scalable**: Modular design, supporting flexible extension and customization

## 🎯 Features

### 🤖 Agent Conversation

- 💬 **Natural Language Chat**: Converse with your knowledge base via `POST /api/v1/chat`
- 🔧 **Tool Calling**: Agent autonomously calls search, stats, and ingest tools as needed
- 🔄 **Multi-turn Dialogue**: Persistent conversation state via PostgreSQL checkpoints (thread_id)
- ⚡ **Streaming SSE**: Real-time token streaming for responsive chat experiences
- 🔌 **Flexible LLM**: Compatible with OpenAI, DeepSeek, Qwen, vLLM, and any OpenAI-compatible API

### 📚 Document Management

- 📥 **Batch Upload**: Support for bulk ingestion of multiple documents simultaneously
- 🏷️ **Metadata Management**: Comprehensive metadata tracking including author, collection, creation date
- 🔄 **Version Control**: Track document revisions and maintain historical versions
- 📁 **Automatic Classification**: Automatic categorization based on content and metadata

### 🔍 Intelligent Retrieval

- 🧠 **Semantic Search**: Context-aware search that understands user intent beyond keyword matching
- 🔍 **Filtered Search**: Advanced filtering by document type, author, collection, date range
- 📊 **Result Ranking**: Intelligent ranking based on relevance score, recency, and user feedback
- 📈 **Search Analytics**: Track search patterns and identify knowledge gaps

### 🏗️ Enterprise Architecture

- 📦 **Scalable Storage**: Milvus cluster support for large-volume document repositories
- 🔄 **Distributed Processing**: Asynchronous document processing pipeline for large-scale ingestion
- 🛡️ **High Availability**: Redundant components and failover mechanisms for reliable critical operations
- 🔒 **Secure**: API Key authentication, data encryption at rest and in transit

## 🚀 Quick Start

### 📋 Prerequisites

- 🐍 Python 3.10+
- 🐳 Docker & Docker Compose (for infrastructure components)
- 💾 Minimum 8GB RAM (16GB recommended for production)

### 📦 Installation Steps

#### 1. Clone the Repository

```bash
git clone https://github.com/zhao11122233/CaraBot.git
cd carabot
```

#### 2. Configure Environment Variables

```bash
# Copy and edit environment variable file
cp .env.example .env
# Edit .env — at minimum change API_KEY to a secure value
```

#### 3. Start Infrastructure

```bash
docker-compose up -d postgres redis milvus-standalone etcd minio
```

#### 4. Initialize Database

```bash
pip install -r requirements.txt
python scripts/init_db.py
```

#### 5. Start Application

```bash
uvicorn src.app.main:create_app --factory --host 0.0.0.0 --port 8000 --reload
```

#### 6. Verify Service

```bash
curl http://localhost:8000/health
```

## 🏗️ Architecture Overview

```mermaid
graph TD
    A[User] --> B[API Gateway]
    B --> C[Authentication Middleware]
    C --> D[Chat API]
    C --> E[Document Management]
    C --> F[Search API]
    C --> G[Stats API]
    
    D --> H[LangGraph Agent]
    H --> I[LLM Provider]
    H --> J[Tools]
    J --> K[Search Service]
    J --> L[Stats Service]
    J --> M[Upload Service]
    
    E --> N[Document Processing]
    E --> O[Metadata Storage]
    N --> P[Vector Embedding]
    P --> Q[Vector Database]
    
    K --> P
    K --> Q
    M --> N
    
    O --> R[PostgreSQL]
    Q --> S[Milvus/Chroma]
    H --> R
```

### 🧩 Technology Stack

| Component | Technology | Description |
|-----------|------------|-------------|
| Web Framework | FastAPI | High-performance asynchronous web framework |
| Agent Framework | LangGraph | ReAct agent with state graph orchestration and checkpoint persistence |
| LLM Integration | OpenAI-compatible API | Supports OpenAI, DeepSeek, Qwen, vLLM, and any compatible provider |
| Vector Database | Milvus/Chroma | Production-grade vector database / Development-grade vector database |
| Relational Database | PostgreSQL | Enterprise-grade relational database + agent conversation checkpoints |
| Cache | Redis | High-performance caching system |
| Vector Embedding | BGE-M3 | Multi-language vector embedding model |
| Document Processing | PyPDF2, python-docx | Multi-format document parsing |
| Containerization | Docker, Kubernetes | Containerized deployment and orchestration |

## 📊 Use Cases

### 🏢 Enterprise Knowledge Management

- 📚 **Internal Wiki**: Central repository for company policies, procedures, and best practices
- 👥 **Employee Onboarding**: New hire documentation and training materials
- 📝 **Technical Documentation**: Software development guides, API documentation, troubleshooting manuals
- 📈 **Sales Enablement**: Product brochures, case studies, competitive intelligence

### 📊 Financial Services

- 📄 **Document Management**: Loan agreements, compliance documents, regulatory filings
- 📊 **Research Reports**: Market analysis, investment research, client presentations
- 🏦 **Policy Retrieval**: Insurance policies, claim procedures, coverage information

### ⚖️ Legal & Compliance

- 📜 **Contract Management**: Search and review contracts by clause, party, or obligation
- 📊 **Compliance Tracking**: Track compliance requirements and audit documentation
- 📚 **Case Law Research**: Legal precedents, court rulings, and statutory references

## 🤝 Contributing

We welcome contributions of all kinds! Please see our [Contributing Guide](CONTRIBUTING.md) for more information.

### 📝 Submitting Code

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### 🐛 Reporting Issues

Please use [GitHub Issues](https://github.com/zhao11122233/CaraBot/issues) to report issues or suggest improvements.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - High-performance asynchronous web framework
- [Milvus](https://milvus.io/) - Open-source vector database
- [LangChain](https://langchain.com/) - LLM application development framework
- [LangGraph](https://langchain-ai.github.io/langgraph/) - Agent orchestration framework
- [BGE-M3](https://github.com/FlagOpen/FlagEmbedding) - Multi-language vector embedding model

## 📞 Contact

- 📱 GitHub: https://github.com/zhao11122233/CaraBot

---

Made with ❤️ by the CaraBot Team

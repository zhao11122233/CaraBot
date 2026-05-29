# CaraBot Agent 智能知识库系统课程大纲

## 🎯 课程目标
掌握基于 LangGraph 的 Agent 智能知识库系统的设计、实现与运维，深入理解 Agent 架构、RAG 检索和 LLM 集成的完整技术栈，成为 AI 应用开发工程师。

## 📚 前置知识
- Python 基础（面向对象、异步编程）
- Java 基础（有助于理解分层架构和设计模式）
- 数据库基础（关系型、非关系型）
- AI 基础（大语言模型、向量嵌入）

## 📂 项目结构概述

```
CaraBot/
├── data/                 # 数据目录
│   ├── chroma/           # Chroma 向量存储数据
│   ├── chroma_v2/        # Chroma v2 版本数据
│   └── carabot.db        # SQLite 数据库（开发环境）
├── logs/                 # 日志目录
│   └── carabot.log       # 应用日志
├── scripts/              # 辅助脚本
│   ├── evaluate.py       # RAG 效果评估脚本
│   └── init_db.py        # 数据库初始化脚本
├── src/                  # 主代码目录
│   └── app/              # 应用核心
│       ├── api/          # API 层
│       │   └── routes/   # 具体路由实现
│       │       ├── chat.py       # Agent 对话接口
│       │       ├── health.py     # 健康检查接口
│       │       ├── search.py     # 语义搜索接口
│       │       ├── stats.py      # 统计信息接口
│       │       └── upload.py     # 文档上传接口
│       ├── core/         # 核心配置和工具
│       │   ├── agent_exceptions.py  # Agent/LLM 异常类
│       │   ├── config.py            # 全局配置
│       │   ├── exceptions.py        # 基础异常类
│       │   └── logging.py           # 日志系统
│       ├── middleware/   # 中间件（认证、日志、错误处理）
│       ├── models/       # 数据模型
│       │   ├── chat_schemas.py  # 对话请求/响应模型
│       │   └── document.py      # 文档元数据模型
│       ├── services/     # 业务逻辑层
│       │   ├── agent_service.py     # LangGraph Agent 核心
│       │   ├── tools.py             # Agent 工具定义
│       │   ├── dedup_service.py     # 文档去重
│       │   ├── document_processor.py # 文档处理
│       │   ├── embedding_service.py # 向量嵌入
│       │   ├── search_service.py    # 语义搜索
│       │   ├── stats_service.py     # 统计聚合
│       │   └── upload_service.py    # 文档上传
│       └── vectorstore/  # 向量存储抽象层
├── tests/                # 测试代码
│   ├── test_chat.py      # Agent 和对话接口测试
│   ├── test_search.py    # 搜索接口测试
│   └── ...
├── .env.example          # 环境变量模板
├── Dockerfile            # Docker 构建文件
├── README.md             # 项目说明
├── requirements.txt      # Python 依赖
└── docker-compose.yml    # Docker Compose 配置
```

### 核心模块说明

1. **API 层** (`src/app/api/routes/`)
   - 处理 HTTP 请求，类似 Java 的 Controller
   - 包含健康检查、文档上传、语义搜索、统计、**Agent 对话** 等接口
   - 使用 FastAPI 的路由装饰器定义接口
   - 新增 `chat.py`：支持 SSE 流式的 Agent 对话端点

2. **Agent 层** (`src/app/services/agent_service.py` + `tools.py`)
   - LangGraph StateGraph 构建的 ReAct Agent，是项目的顶层编排核心
   - `AgentService`：图构建、Checkpoint 管理、run/stream 执行
   - `tools.py`：Agent 工具工厂，将现有服务包装为 LLM 可调用的工具
   - 三个内置工具：搜索知识库、查统计、文本入录
   - 对话状态通过 PostgreSQL Checkpoint 持久化

3. **服务层** (`src/app/services/`)
   - 实现业务逻辑，类似 Java 的 Service
   - `UploadService`：处理文档上传的完整流程（解析→分块→嵌入→入库）
   - `SearchService`：处理语义相似性搜索
   - `EmbeddingService`：封装 BGE-m3 向量嵌入模型

4. **向量存储层** (`src/app/vectorstore/`)
   - 抽象向量数据库操作，支持 Milvus 和 Chroma
   - `BaseVectorStore`：定义统一接口
   - `MilvusStore`：生产环境向量存储
   - `ChromaStore`：开发环境向量存储

5. **核心配置** (`src/app/core/config.py`)
   - 管理所有配置项，类似 Spring 的 application.properties
   - 使用 Pydantic Settings 从环境变量加载配置
   - 启动时自动验证配置完整性
   - 新增 LLM 配置组（base_url、api_key、model 等）和 Agent 配置组

---

## 🚀 第一阶段：项目入门与基础（5 课）

### 第 1 课：项目介绍与环境搭建
- CaraBot 项目定位与核心特性
- Python 3.10+ 环境安装
- 项目克隆与依赖安装
- 学习时长：1-2 天
- 实践任务：成功搭建开发环境

### 第 2 课：快速启动与核心功能体验
- 配置环境变量（.env 文件）
- 启动 FastAPI 服务
- 使用 Swagger UI 体验核心功能
- 学习时长：1 天
- 实践任务：成功上传并搜索文档

### 第 3 课：项目结构与代码组织
- 完整目录结构解析
- 核心文件作用说明
- 与 Java Spring Boot 项目的对比
- 学习时长：1 天
- 实践任务：绘制项目架构图

### 第 4 课：FastAPI 框架基础
- FastAPI 核心特性介绍
- 路由与请求处理
- 响应模型与数据验证
- 学习时长：1 天
- 实践任务：编写简单的 FastAPI 接口

### 第 5 课：配置系统与环境变量
- Pydantic Settings 详解
- 环境变量加载机制
- 配置验证与错误处理
- 学习时长：1 天
- 实践任务：自定义配置项并验证

---

## 🧱 第二阶段：核心架构与设计模式（6 课）

### 第 6 课：分层架构设计
- API 层、服务层、数据层的职责
- 依赖注入机制（FastAPI Depends）
- 面向接口编程的实践
- 学习时长：2 天
- 实践任务：分析请求处理流程

### 第 7 课：工厂模式与抽象基类
- 向量存储工厂（get_vector_store）
- BaseVectorStore 抽象接口
- 多态与代码解耦
- 学习时长：2 天
- 实践任务：添加新的向量存储支持

### 第 8 课：中间件机制
- 认证中间件（AuthGuard）
- 请求日志中间件
- 全局错误处理
- 学习时长：1 天
- 实践任务：自定义中间件

### 第 9 课：异步编程在 Python 中的应用
- async/await 语法
- 异步数据库操作
- 同步代码异步化技巧
- 学习时长：2 天
- 实践任务：将同步代码改为异步

### 第 10 课：数据模型与 ORM
- SQLAlchemy 异步使用
- 数据模型定义
- 数据库迁移与初始化
- 学习时长：2 天
- 实践任务：定义新的数据模型

### 第 11 课：日志系统与监控
- 结构化 JSON 日志
- 分布式追踪（trace_id）
- 健康检查接口详解
- 学习时长：1 天
- 实践任务：分析日志结构

---

## 🧠 第三阶段：RAG 核心技术（8 课）

### 第 12 课：文档处理流水线
- 文件上传与接收
- 文件类型检测与解析
- 文档分块策略与实现
- 学习时长：2 天
- 实践任务：调试文档分块过程

### 第 13 课：文档去重机制
- SHA256 哈希计算
- 关系数据库去重记录
- 增量更新与版本管理
- 学习时长：2 天
- 实践任务：测试文档去重功能

### 第 14 课：向量嵌入技术
- BGE-m3 模型介绍
- 文本向量嵌入的原理
- EmbeddingService 实现详解
- 学习时长：3 天
- 实践任务：使用不同模型生成向量

### 第 15 课：向量数据库基础
- 向量空间模型与相似性计算
- 向量数据库与传统数据库的差异
- 常见向量数据库对比
- 学习时长：2 天
- 实践任务：对比不同向量数据库的查询结果

### 第 16 课：Chroma 向量存储（开发环境）
- Chroma 快速入门
- 本地文件存储机制
- 开发环境使用场景
- 学习时长：1 天
- 实践任务：使用 Chroma 进行向量操作

### 第 17 课：Milvus 向量存储（生产环境）
- Milvus 分布式架构
- 集合与分区管理
- 生产环境部署建议
- 学习时长：2 天
- 实践任务：部署 Milvus 并测试

### 第 18 课：相似性搜索优化
- 搜索参数调优（top_k、threshold）
- 过滤与排序策略
- 搜索性能优化技巧
- 学习时长：2 天
- 实践任务：优化搜索性能

### 第 19 课：RAG 效果评估
- Recall@k 指标详解
- badcase 分析方法
- evaluate.py 脚本使用
- 学习时长：2 天
- 实践任务：评估 RAG 效果并分析 badcase

### 第 20 课：Agent 架构与 LangGraph 框架
- Agent 设计理念与 ReAct 模式
- LangGraph StateGraph 核心概念：状态、节点、边
- CaraBot 的 Agent 图结构解析（call_model ⇄ call_tools）
- 与 Java 工作流框架（Camunda、Flowable）的对比
- 学习时长：3 天
- 实践任务：手绘 Agent 图结构并跟踪一次请求的完整执行路径

### 第 21 课：工具定义与集成
- LangChain Tool 装饰器的使用
- 将现有服务包装为 Agent 工具
- 工具输入 Schema 设计（Pydantic 模型）
- 工具结果格式化（让 LLM 能正确理解输出）
- 学习时长：2 天
- 实践任务：为 Agent 添加一个新工具

### 第 22 课：LLM 集成与多轮对话
- OpenAI 兼容接口的使用（ChatOpenAI + bind_tools）
- 流式（SSE）与非流式响应的实现
- 对话状态管理与 Checkpoint 持久化
- thread_id 对话关联机制
- 学习时长：3 天
- 实践任务：实现多轮对话并验证状态恢复

---

## 🔧 第四阶段：功能扩展与性能优化（5 课）

### 第 23 课：多格式文档支持
- PDF、DOCX、Markdown 解析
- 自定义文档处理器
- 文档格式扩展方法
- 学习时长：2 天
- 实践任务：添加新的文档格式支持

### 第 24 课：多语言支持
- 多语言嵌入模型选择
- 语言检测与处理
- 跨语言搜索实践
- 学习时长：2 天
- 实践任务：测试跨语言搜索功能

### 第 25 课：缓存与性能优化
- Redis 缓存集成
- 热点数据缓存策略
- 系统性能瓶颈分析
- 学习时长：2 天
- 实践任务：添加缓存优化性能

### 第 26 课：安全与权限控制
- API Key 认证机制
- 请求频率限制
- 数据加密与隐私保护
- 学习时长：1 天
- 实践任务：加强 API 安全

### 第 27 课：Agent 进阶与多模型适配
- Agent 系统提示词工程与优化
- 多 LLM 提供商适配（OpenAI、DeepSeek、Qwen、本地模型）
- Tool 调用失败处理与重试策略
- 学习时长：3 天
- 实践任务：切换 LLM 提供商并对比 Agent 表现

---

## 🚢 第五阶段：部署与运维（7 课）

### 第 28 课：容器化部署
- Docker 镜像构建
- Docker Compose 编排
- 基础设施容器化（PostgreSQL、Redis、Milvus）
- 学习时长：2 天
- 实践任务：使用 Docker 部署系统

### 第 29 课：生产环境配置
- 环境隔离（开发、测试、生产）
- 配置中心集成
- 高可用架构设计
- 学习时长：2 天
- 实践任务：配置生产环境

### 第 30 课：监控与告警
- Prometheus 指标采集
- Grafana 可视化
- Agent 调用链追踪（LangSmith/LangFuse）
- 异常告警配置
- 学习时长：2 天
- 实践任务：搭建监控系统

### 第 31 课：日志管理
- ELK 日志栈集成
- 日志分析与故障排查
- 日志轮转与清理
- 学习时长：1 天
- 实践任务：分析应用日志

### 第 32 课：备份与恢复
- 数据库备份策略
- 向量数据备份
- Checkpoint 对话记录的备份
- 灾难恢复演练
- 学习时长：1 天
- 实践任务：制定备份恢复计划

### 第 33 课：项目实战与总结
- 从 0 到 1 搭建 Agent 驱动的知识库系统
- 常见问题与解决方案
- 未来发展与技术趋势（Multi-Agent、GraphRAG）
- 学习时长：3 天
- 实践任务：完成一个完整的 Agent 知识库项目

---

## 📅 学习计划建议
- 总共 33 课（新增 3 课 Agent 专题），约 3-4 个月完成全部课程
- 每课配套实践作业，巩固所学知识
- 课程结束后完成一个完整的 Agent 知识库项目实战

## 📝 学习方法建议

1. **从 API 入手**
   - 先看 `src/app/api/routes/` 下的接口实现，了解系统能做什么
   - 跟踪请求的处理流程，从 API 到服务层再到数据层

2. **对比学习**
   - 用 Java 的知识类比 Python 的代码结构
   - 对比关系数据库和向量数据库的差异
   - 理解同步编程和异步编程的区别

3. **动手实践**
   - 不要只看代码，要动手运行和修改
   - 尝试添加新的功能或优化现有功能
   - 用不同的文档格式测试系统

4. **深入原理**
   - 学习向量空间模型和相似性计算
   - 理解 RAG 系统的优缺点
   - 关注向量数据库的最新发展

5. **深入原理**
   - 学习 Agent 设计模式（ReAct、Plan-Execute、Multi-Agent）
   - 理解 LangGraph 的状态图和 Checkpoint 机制
   - 关注 Agent 编排的最新发展（GraphRAG、Agentic RAG）

6. **问题排查**
   - 遇到问题先查看官方文档和代码注释
   - 利用搜索引擎寻找解决方案
   - 记录问题和解决方法，形成知识库

## 📚 参考资料
- FastAPI 官方文档：https://fastapi.tiangolo.com/
- Milvus 官方文档：https://milvus.io/docs
- LangChain 文档：https://python.langchain.com/
- LangGraph 文档：https://langchain-ai.github.io/langgraph/
- BGE-m3 模型：https://huggingface.co/BAAI/bge-m3
- OpenAI API 文档：https://platform.openai.com/docs

## 🎯 学习成果
- 掌握企业级 Agent 知识库系统的完整开发流程
- 深入理解 LangGraph Agent 架构、工具调用和状态管理
- 能够独立设计和实现 Agent 驱动的 AI 应用
- 具备多轮对话、流式响应和 LLM 集成的实战能力
- 具备生产环境部署和运维能力
- 了解 AI 应用的性能优化和安全最佳实践
- 能够将 Agent + RAG 系统集成到实际业务中

---

**提示**：学习过程中遇到问题，先看官方文档和代码注释，再搜索解决方案。多动手实践，多思考为什么要这样设计，而不是只看怎么做。
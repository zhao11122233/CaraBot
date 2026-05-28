# CaraBot 企业级 RAG 系统课程
## 第 4 课：FastAPI 框架基础

### 🎯 本节课目标
- 了解 FastAPI 的核心特性和优势
- 掌握 FastAPI 的路由与请求处理
- 学习响应模型与数据验证
- 对比 FastAPI 与 Spring Boot 的差异
- 学习时长：1 天
- 实践任务：编写简单的 FastAPI 接口

---

## 1. FastAPI 简介

### 1.1 什么是 FastAPI？

FastAPI 是一个现代、快速（高性能）的 Web 框架，用于构建 API 接口。它基于 Python 3.6+ 的类型提示，自动生成交互式 API 文档，支持异步处理，性能非常高。

### 1.2 FastAPI 的核心特性

#### 1.2.1 快速
- **异步支持**：基于 Starlette 框架，支持异步处理，性能非常高
- **吞吐量**：可以处理大量的并发请求，适合高流量的场景
- **响应时间**：响应时间非常短，用户体验好

#### 1.2.2 高效
- **自动文档**：自动生成交互式 API 文档（Swagger UI 和 ReDoc）
- **类型提示**：使用 Python 的类型提示，自动进行数据验证和序列化
- **快速开发**：可以快速开发出高质量的 API 接口

#### 1.2.3 易用
- **简单直观**：API 设计简单直观，容易理解和使用
- **文档完善**：文档非常完善，有很多例子和教程
- **社区支持**：社区活跃，有大量的第三方库和工具

#### 1.2.4 类型安全
- **数据验证**：自动验证请求参数的类型和格式
- **错误提示**：提供清晰的错误提示，便于调试
- **代码质量**：类型提示可以提升代码的质量和可维护性

#### 1.2.5 可扩展
- **中间件支持**：支持中间件，可以扩展框架的功能
- **插件系统**：有很多第三方插件，可以快速扩展功能
- **集成性好**：可以与很多其他库和框架集成，比如 SQLAlchemy、Redis 等

### 1.3 FastAPI 的性能

FastAPI 的性能非常高，与 Node.js 和 Go 相当，是 Python 中性能最好的 Web 框架之一。

#### 性能对比
| 框架 | 语言 | 性能（请求/秒） |
|------|------|----------------|
| FastAPI | Python | ~10000 |
| Starlette | Python | ~12000 |
| Flask | Python | ~4000 |
| Django | Python | ~3000 |
| Express | Node.js | ~10000 |
| Gin | Go | ~25000 |

#### 为什么 FastAPI 这么快？
- **异步支持**：基于 Starlette 框架，支持异步处理
- **高效的路由匹配**：使用 Radix 树算法进行路由匹配
- **减少中间件开销**：中间件设计高效，减少不必要的开销
- **使用 Pydantic 进行数据验证**：Pydantic 是一个高性能的数据验证库

---

## 2. 路由与请求处理

### 2.1 基本路由

#### 2.1.1 定义路由
```python
from fastapi import FastAPI

app = FastAPI(title="CaraBot API", version="1.0.0")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.post("/api/v1/upload")
async def upload_file():
    """Upload file endpoint."""
    return {"message": "File uploaded successfully"}

@app.get("/api/v1/search")
async def search_documents():
    """Search documents endpoint."""
    return {"results": []}
```

#### 2.1.2 路由方法
FastAPI 支持所有 HTTP 方法：
- **GET**：用于获取资源
- **POST**：用于创建资源
- **PUT**：用于更新资源
- **DELETE**：用于删除资源
- **PATCH**：用于部分更新资源
- **OPTIONS**：用于获取资源的选项
- **HEAD**：用于获取资源的头部信息

### 2.2 路径参数

#### 2.2.1 基本路径参数
```python
@app.get("/api/v1/documents/{document_id}")
async def get_document(document_id: str):
    """Get document by ID."""
    return {"document_id": document_id, "content": "Document content"}
```

#### 2.2.2 路径参数验证
```python
from fastapi import Path

@app.get("/api/v1/documents/{document_id}")
async def get_document(
    document_id: str = Path(..., min_length=36, max_length=36, description="Document ID (UUID)"),
):
    """Get document by ID."""
    return {"document_id": document_id, "content": "Document content"}
```

### 2.3 查询参数

#### 2.3.1 基本查询参数
```python
@app.get("/api/v1/search")
async def search_documents(query: str, top_k: int = 5):
    """Search documents by query."""
    return {"query": query, "top_k": top_k, "results": []}
```

#### 2.3.2 查询参数验证
```python
from fastapi import Query

@app.get("/api/v1/search")
async def search_documents(
    query: str = Query(..., min_length=1, max_length=100, description="Search query"),
    top_k: int = Query(5, ge=1, le=100, description="Number of results to return"),
    threshold: float = Query(0.7, ge=0.0, le=1.0, description="Similarity threshold"),
):
    """Search documents by query."""
    return {"query": query, "top_k": top_k, "threshold": threshold, "results": []}
```

### 2.4 请求体

#### 2.4.1 基本请求体
```python
from pydantic import BaseModel

class SearchRequest(BaseModel):
    """Search request model."""
    query: str
    top_k: int = 5
    threshold: float = 0.7

@app.post("/api/v1/search")
async def search_documents(request: SearchRequest):
    """Search documents by query."""
    return {
        "query": request.query,
        "top_k": request.top_k,
        "threshold": request.threshold,
        "results": []
    }
```

#### 2.4.2 复杂请求体
```python
from pydantic import BaseModel, Field
from typing import List, Optional

class Metadata(BaseModel):
    """Document metadata."""
    author: Optional[str] = None
    collection: Optional[str] = None
    tags: List[str] = []

class UploadRequest(BaseModel):
    """Upload request model."""
    filename: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    metadata: Optional[Metadata] = None

@app.post("/api/v1/upload")
async def upload_file(request: UploadRequest):
    """Upload file endpoint."""
    return {
        "filename": request.filename,
        "content_length": len(request.content),
        "metadata": request.metadata.dict() if request.metadata else None
    }
```

### 2.5 文件上传

#### 2.5.1 单文件上传
```python
from fastapi import File, UploadFile

@app.post("/api/v1/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload file endpoint."""
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "file_size": len(await file.read())
    }
```

#### 2.5.2 多文件上传
```python
from fastapi import File, UploadFile
from typing import List

@app.post("/api/v1/upload-multiple")
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    """Upload multiple files endpoint."""
    results = []
    for file in files:
        content = await file.read()
        results.append({
            "filename": file.filename,
            "content_type": file.content_type,
            "file_size": len(content)
        })
    return {"files": results}
```

---

## 3. 响应模型与数据验证

### 3.1 响应模型

#### 3.1.1 基本响应模型
```python
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class DocumentResponse(BaseModel):
    """Document response model."""
    document_id: str
    filename: str
    content: str
    author: Optional[str] = None
    collection: Optional[str] = None
    created_at: datetime
    updated_at: datetime

@app.get("/api/v1/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str):
    """Get document by ID."""
    return {
        "document_id": document_id,
        "filename": "test.pdf",
        "content": "Document content",
        "author": "John Doe",
        "collection": "default",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
```

#### 3.1.2 响应模型配置
```python
from pydantic import BaseModel, ConfigDict
from typing import Optional

class DocumentResponse(BaseModel):
    """Document response model."""
    model_config = ConfigDict(from_attributes=True)

    document_id: str
    filename: str
    content: str
    author: Optional[str] = None
    collection: Optional[str] = None

# 从 ORM 模型转换
@app.get("/api/v1/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str):
    """Get document by ID."""
    # 假设这是从数据库查询到的 ORM 模型
    document = Document(
        id=document_id,
        filename="test.pdf",
        content="Document content",
        author="John Doe",
        collection="default"
    )
    return document
```

### 3.2 数据验证

#### 3.2.1 基本数据验证
```python
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional

class SearchRequest(BaseModel):
    """Search request model."""
    query: str = Field(..., min_length=1, max_length=100, description="Search query")
    top_k: int = Field(5, ge=1, le=100, description="Number of results to return")
    threshold: float = Field(0.7, ge=0.0, le=1.0, description="Similarity threshold")
    filters: Optional[List[str]] = Field(None, max_items=10, description="Search filters")

# 验证请求体
@app.post("/api/v1/search")
async def search_documents(request: SearchRequest):
    """Search documents by query."""
    return {
        "query": request.query,
        "top_k": request.top_k,
        "threshold": request.threshold,
        "filters": request.filters,
        "results": []
    }
```

#### 3.2.2 自定义验证
```python
from pydantic import BaseModel, Field, field_validator
from typing import str

class UploadRequest(BaseModel):
    """Upload request model."""
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., min_length=1)

    @field_validator("filename")
    def filename_must_contain_dot(cls, v):
        """Validate filename must contain dot."""
        if "." not in v:
            raise ValueError("Filename must contain dot")
        return v

    @field_validator("content_type")
    def content_type_must_be_valid(cls, v):
        """Validate content type is valid."""
        valid_content_types = ["application/pdf", "application/msword", "text/plain"]
        if v not in valid_content_types:
            raise ValueError(f"Invalid content type. Must be one of: {valid_content_types}")
        return v
```

### 3.3 错误处理

#### 3.3.1 基本错误处理
```python
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/api/v1/documents/{document_id}")
async def get_document(document_id: str):
    """Get document by ID."""
    # 假设文档不存在
    if document_id != "valid-id":
        raise HTTPException(
            status_code=404,
            detail=f"Document with ID '{document_id}' not found",
            headers={"X-Error": "DocumentNotFound"}
        )
    return {"document_id": document_id, "content": "Document content"}
```

#### 3.3.2 自定义异常
```python
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI()

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "code": exc.status_code}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handle validation exceptions."""
    return JSONResponse(
        status_code=422,
        content={"error": "Validation error", "details": exc.errors()}
    )
```

---

## 4. 依赖注入

### 4.1 基本依赖注入

#### 4.1.1 定义依赖
```python
from fastapi import FastAPI, Depends

app = FastAPI()

def get_api_key(api_key: str = Depends()):
    """Get API key from dependencies."""
    if api_key != "secret-key":
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key

@app.get("/api/v1/protected")
async def protected_route(api_key: str = Depends(get_api_key)):
    """Protected endpoint."""
    return {"message": "Access granted", "api_key": api_key}
```

#### 4.1.2 类依赖
```python
from fastapi import FastAPI, Depends
from typing import Optional

app = FastAPI()

class Database:
    """Database dependency."""
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.connection = None
    
    def connect(self):
        """Connect to database."""
        self.connection = f"Connected to {self.db_url}"
        return self.connection
    
    def disconnect(self):
        """Disconnect from database."""
        self.connection = None

def get_database(db_url: str = "postgresql://localhost:5432/carabot"):
    """Get database instance."""
    db = Database(db_url)
    db.connect()
    try:
        yield db
    finally:
        db.disconnect()

@app.get("/api/v1/db-status")
async def db_status(db: Database = Depends(get_database)):
    """Get database status."""
    return {"db_url": db.db_url, "connection_status": db.connection}
```

### 4.2 依赖链

```python
from fastapi import FastAPI, Depends, HTTPException

app = FastAPI()

def get_api_key(api_key: str = Depends()):
    """Get API key from dependencies."""
    if api_key != "secret-key":
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key

def get_user(api_key: str = Depends(get_api_key)):
    """Get user from API key."""
    # 假设从数据库查询用户
    user = {"id": 1, "name": "John Doe", "api_key": api_key}
    return user

@app.get("/api/v1/user-profile")
async def user_profile(user: dict = Depends(get_user)):
    """Get user profile."""
    return {"user": user}
```

---

## 5. 与 Spring Boot 的对比

### 5.1 项目结构对比

| FastAPI | Spring Boot | 说明 |
|---------|-------------|------|
| 路由装饰器 | `@GetMapping`、`@PostMapping` 等注解 | 定义 API 接口 |
| Pydantic 模型 | `@RequestBody`、`@ResponseBody` | 请求和响应模型 |
| Depends | `@Autowired`、构造函数注入 | 依赖注入 |
| 中间件 | 过滤器、拦截器 | 处理横切关注点 |
| 自动文档 | Springfox、SpringDoc | 生成 API 文档 |
| `requirements.txt` | `pom.xml`、`build.gradle` | 依赖管理 |
| `.env` | `application.properties`、`application.yml` | 环境变量配置 |

### 5.2 开发效率对比

| 特性 | FastAPI | Spring Boot |
|------|---------|-------------|
| 开发速度 | 快，代码简洁，无需编译 | 较慢，代码冗长，需要编译 |
| 自动文档 | 自动生成 Swagger UI 和 ReDoc | 需要手动配置 Springfox 或 SpringDoc |
| 数据验证 | 自动进行数据验证，基于类型提示 | 需要手动添加 `@Valid` 和 `@NotBlank` 等注解 |
| 错误提示 | 清晰的错误提示，便于调试 | 错误提示较为复杂，需要查看日志 |
| 学习曲线 | 平缓，容易上手 | 陡峭，需要掌握大量概念 |

### 5.3 性能对比

| 特性 | FastAPI | Spring Boot |
|------|---------|-------------|
| 运行速度 | 快，异步支持 | 快，编译执行 |
| 吞吐量 | 高，可以处理大量并发请求 | 高，适合高流量场景 |
| 内存占用 | 较低 | 较高 |
| 启动时间 | 快，秒级启动 | 较慢，通常需要几秒到十几秒 |

---

## 6. 课后作业

1. **编写 FastAPI 接口**：编写至少 3 个不同类型的接口（GET、POST、PUT、DELETE）
2. **数据验证**：为接口添加数据验证，包括路径参数、查询参数和请求体
3. **响应模型**：为接口定义响应模型，确保返回的数据格式正确
4. **依赖注入**：实现一个简单的依赖注入，比如数据库连接
5. **错误处理**：为接口添加错误处理，返回清晰的错误信息
6. **对比 Spring Boot**：对比 FastAPI 与 Spring Boot 的差异，列出至少 5 个不同点

---

## 📚 扩展阅读
- FastAPI 官方文档：https://fastapi.tiangolo.com/
- Starlette 官方文档：https://www.starlette.io/
- Pydantic 官方文档：https://docs.pydantic.dev/
- FastAPI 教程：https://fastapi.tiangolo.com/tutorial/

---

**下节课预告**：第 5 课 - 配置系统与环境变量
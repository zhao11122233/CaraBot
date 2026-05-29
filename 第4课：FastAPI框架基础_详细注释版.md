# CaraBot 企业级 RAG 系统课程
## 第 4 课：FastAPI 框架基础_详细注释版

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
# 导入FastAPI类，这是整个应用的入口点
# 类比：如果你把FastAPI想象成一个网站容器，这个类就是这个容器的蓝图
from fastapi import FastAPI

# 创建FastAPI应用实例
# title和version是可选参数，会显示在自动生成的API文档中
# 类比：这就像在创建一个Web服务器实例，准备好接收请求
app = FastAPI(title="CaraBot API", version="1.0.0")

# 定义GET请求路由：/health
# @app.get()是装饰器，作用是告诉FastAPI：
# "当有人用GET方法访问/health这个URL时，请调用下面的health_check函数"
# async关键字表示这是一个异步函数，可以处理高并发请求
# 类比：这就像在给一个房间挂上门牌，上面写着"GET请求 /health 请进"
@app.get("/health")
async def health_check():
    """健康检查接口：用于测试服务是否正常运行"""
    # 返回一个Python字典，FastAPI会自动将其转换为JSON格式的HTTP响应
    # 类比：这就像房间主人对访客说的话，然后FastAPI帮你翻译成标准格式
    return {"status": "healthy"}

# 定义POST请求路由：/api/v1/upload
# POST方法通常用于创建新资源或上传数据
@app.post("/api/v1/upload")
async def upload_file():
    """文件上传接口：用于接收用户上传的文件"""
    return {"message": "File uploaded successfully"}

# 定义GET请求路由：/api/v1/search
# GET方法通常用于查询或获取数据
@app.get("/api/v1/search")
async def search_documents():
    """搜索文档接口：用于根据关键词搜索文档"""
    return {"results": []}
```

#### 2.1.2 路由方法
FastAPI 支持所有 HTTP 方法：
- **GET**：用于获取资源（查询数据）
- **POST**：用于创建资源（添加数据）
- **PUT**：用于更新资源（修改数据，完整替换）
- **DELETE**：用于删除资源
- **PATCH**：用于部分更新资源（修改数据，只改部分字段）
- **OPTIONS**：用于获取资源的选项
- **HEAD**：用于获取资源的头部信息（不带响应体）

### 2.2 路径参数

#### 2.2.1 基本路径参数
```python
# 定义带路径参数的GET路由
# {document_id}是路径参数，URL示例：/api/v1/documents/12345
# 类比：这就像快递地址，/api/v1/documents是区域，{document_id}是具体门牌号
@app.get("/api/v1/documents/{document_id}")
# 函数参数document_id: str指定参数类型为字符串
# 注意：路径参数名必须和URL中的参数名一致
# 类比：FastAPI会从URL中把"门牌号"提取出来，作为参数传给这个函数
async def get_document(document_id: str):
    """根据ID获取文档：传入文档ID，返回对应文档内容"""
    # 使用路径参数构建响应
    return {"document_id": document_id, "content": "Document content"}
```

#### 2.2.2 路径参数验证
```python
# 导入Path类，用于对路径参数进行更严格的验证
# Path是FastAPI提供的工具类，专门用来验证路径参数
from fastapi import Path

@app.get("/api/v1/documents/{document_id}")
# 使用Path类进行验证
# 参数说明：
# - ... 表示这个参数是必填的（没有默认值）
# - min_length=36, max_length=36 限定字符串长度必须是36位（符合UUID格式）
# - description 会显示在API文档中，告诉使用者这个参数的作用
async def get_document(
    document_id: str = Path(..., min_length=36, max_length=36, description="文档ID（UUID格式）"),
):
    """根据ID获取文档：文档ID必须是36位UUID格式"""
    return {"document_id": document_id, "content": "Document content"}
```

### 2.3 查询参数

#### 2.3.1 基本查询参数
```python
# 定义带查询参数的GET路由
# 查询参数是URL中?后面的部分，示例：/api/v1/search?query=python&top_k=10
# 类比：这就像填写表单，query是搜索关键词，top_k是想要显示的结果数量
@app.get("/api/v1/search")
# 函数参数说明：
# - query: str 是必填的字符串参数，没有默认值
# - top_k: int = 5 是可选的整数参数，默认值为5
# 注意：查询参数名必须和函数参数名一致
async def search_documents(query: str, top_k: int = 5):
    """搜索文档：传入关键词，返回相关文档列表"""
    return {"query": query, "top_k": top_k, "results": []}
```

#### 2.3.2 查询参数验证
```python
# 导入Query类，用于对查询参数进行验证
# Query和Path类似，都是FastAPI提供的验证工具类
from fastapi import Query

@app.get("/api/v1/search")
# 使用Query类对每个查询参数进行详细验证
# 参数说明：
# - ge: greater than or equal，大于等于
# - le: less than or equal，小于等于
async def search_documents(
    # query：必填字符串，长度1-100个字符
    query: str = Query(..., min_length=1, max_length=100, description="搜索关键词"),
    # top_k：可选整数，默认5，取值范围1-100
    top_k: int = Query(5, ge=1, le=100, description="返回结果数量"),
    # threshold：可选浮点数，默认0.7，取值范围0.0-1.0
    threshold: float = Query(0.7, ge=0.0, le=1.0, description="相似度阈值"),
):
    """搜索文档：支持关键词、结果数量和相似度阈值参数"""
    return {"query": query, "top_k": top_k, "threshold": threshold, "results": []}
```

### 2.4 请求体

#### 2.4.1 基本请求体
```python
# 导入BaseModel类，这是Pydantic库的核心类
# Pydantic是一个数据验证和序列化库，FastAPI用它来处理请求和响应数据
# 类比：BaseModel就像一个数据模板，规定了数据应该有什么字段、什么类型
from pydantic import BaseModel

# 定义搜索请求的数据模型，继承自BaseModel
# 这个类定义了请求体应该包含的字段和类型
class SearchRequest(BaseModel):
    """搜索请求模型：定义了搜索接口接收的数据格式"""
    # 必填字段：字符串类型，没有默认值
    query: str
    # 可选字段：整数类型，默认值为5
    top_k: int = 5
    # 可选字段：浮点数类型，默认值为0.7
    threshold: float = 0.7

# 定义POST路由，用于接收搜索请求
# 注意：POST请求通常用于发送较复杂的数据（如JSON），这些数据放在请求体中
@app.post("/api/v1/search")
# request: SearchRequest 告诉FastAPI：
# "请把请求体中的JSON数据解析成SearchRequest类的实例，赋值给request变量"
# FastAPI会自动完成：
# 1. 从请求中读取JSON数据
# 2. 验证数据是否符合SearchRequest的定义
# 3. 如果验证失败，返回清晰的错误信息
# 4. 如果验证成功，创建SearchRequest实例
async def search_documents(request: SearchRequest):
    """搜索文档接口：接收搜索请求，返回搜索结果"""
    # 使用request.字段名访问各个字段的值
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

# 定义元数据子模型（嵌套模型）
# 这个模型会作为UploadRequest模型的一部分
class Metadata(BaseModel):
    """文档元数据：包含作者、集合、标签等信息"""
    # Optional[str]表示可选的字符串，默认值为None（可以不提供）
    author: Optional[str] = None
    collection: Optional[str] = None
    # List[str]表示字符串列表，默认值为空列表
    tags: List[str] = []

# 定义上传请求主模型
class UploadRequest(BaseModel):
    """上传请求模型：定义了文件上传接口接收的数据格式"""
    # 使用Field类进行更详细的字段配置
    # ... 表示必填，min_length=1 表示至少1个字符，max_length=255 表示最多255个字符
    filename: str = Field(..., min_length=1, max_length=255, description="文件名")
    content: str = Field(..., min_length=1, description="文件内容")
    # 可选的Metadata类型字段，默认值为None
    metadata: Optional[Metadata] = None

@app.post("/api/v1/upload")
async def upload_file(request: UploadRequest):
    """文件上传接口：接收文件内容和元数据"""
    return {
        "filename": request.filename,
        "content_length": len(request.content),
        # 条件表达式：如果metadata不为None，就调用dict()方法转换成字典
        # 如果metadata为None，就直接返回None
        "metadata": request.metadata.dict() if request.metadata else None
    }
```

### 2.5 文件上传

#### 2.5.1 单文件上传
```python
# 导入File和UploadFile类，用于处理文件上传
# UploadFile是FastAPI提供的类，代表一个上传的文件
from fastapi import File, UploadFile

@app.post("/api/v1/upload")
# file: UploadFile = File(...) 表示这是一个文件上传字段
# File(...)表示这是必填的文件上传字段
# UploadFile对象提供了方便的方法来访问文件名、文件类型和读取文件内容
async def upload_file(file: UploadFile = File(...)):
    """单文件上传接口：接收并处理单个上传文件"""
    return {
        "filename": file.filename,  # 获取上传文件的原始文件名
        "content_type": file.content_type,  # 获取文件的MIME类型（如text/plain, image/png）
        "file_size": len(await file.read())  # 使用await读取文件内容并计算大小
        # 注意：file.read()是异步操作，所以需要await关键字
    }
```

#### 2.5.2 多文件上传
```python
from fastapi import File, UploadFile
from typing import List

@app.post("/api/v1/upload-multiple")
# files: List[UploadFile] 表示这是一个UploadFile类型的列表
# 即可以同时上传多个文件
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    """多文件上传接口：同时接收并处理多个上传文件"""
    results = []
    # 遍历所有上传的文件
    for file in files:
        # 读取文件内容
        content = await file.read()
        # 为每个文件构建结果信息
        results.append({
            "filename": file.filename,
            "content_type": file.content_type,
            "file_size": len(content)
        })
    # 返回所有文件的处理结果
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

# 定义文档响应模型
# 响应模型的作用：
# 1. 规定返回给客户端的JSON格式
# 2. 自动对返回数据进行类型转换和验证
# 3. 在API文档中清晰地展示响应格式
class DocumentResponse(BaseModel):
    """文档响应模型：定义了获取文档接口返回的数据格式"""
    document_id: str
    filename: str
    content: str
    author: Optional[str] = None
    collection: Optional[str] = None
    created_at: datetime  # 日期时间类型，Pydantic会自动处理
    updated_at: datetime

# 定义GET路由，并指定响应模型为DocumentResponse
# response_model=DocumentResponse 告诉FastAPI：
# "请把返回的数据转换成DocumentResponse格式，然后再返回给客户端"
@app.get("/api/v1/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str):
    """根据ID获取文档接口"""
    # 返回一个Python字典
    # FastAPI会自动：
    # 1. 把这个字典转换成DocumentResponse实例
    # 2. 验证数据是否符合DocumentResponse的定义
    # 3. 转换成JSON格式返回
    return {
        "document_id": document_id,
        "filename": "test.pdf",
        "content": "Document content",
        "author": "John Doe",
        "collection": "default",
        "created_at": datetime.utcnow(),  # 获取当前UTC时间
        "updated_at": datetime.utcnow()
    }
```

#### 3.1.2 响应模型配置
```python
from pydantic import BaseModel, ConfigDict
from typing import Optional

class DocumentResponse(BaseModel):
    """文档响应模型：支持从ORM对象属性获取数据"""
    # ConfigDict配置：from_attributes=True
    # 这个配置的作用是：允许从对象的属性获取数据，而不仅限于字典
    # 这样就可以直接返回数据库的ORM对象，而不需要手动转换成字典
    model_config = ConfigDict(from_attributes=True)

    document_id: str
    filename: str
    content: str
    author: Optional[str] = None
    collection: Optional[str] = None

# 从ORM模型转换
@app.get("/api/v1/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str):
    """根据ID获取文档接口：直接返回ORM对象"""
    # 假设这是从数据库查询到的ORM对象（比如SQLAlchemy的模型实例）
    # ORM对象有id, filename, content, author, collection等属性
    document = Document(
        id=document_id,
        filename="test.pdf",
        content="Document content",
        author="John Doe",
        collection="default"
    )
    # 直接返回ORM对象
    # 因为配置了from_attributes=True，FastAPI会自动：
    # 1. 从document对象的属性读取数据
    # 2. 转换成DocumentResponse格式
    return document
```

### 3.2 数据验证

#### 3.2.1 基本数据验证
```python
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional

class SearchRequest(BaseModel):
    """搜索请求模型：包含完整的数据验证规则"""
    # 使用Field类对字段进行详细配置
    # 参数说明：
    # - ... 表示必填字段
    # - min_length, max_length 限制字符串长度
    # - ge, le 限制数值范围
    # - max_items 限制列表元素数量
    # - description 字段描述，会显示在API文档中
    query: str = Field(..., min_length=1, max_length=100, description="搜索关键词")
    top_k: int = Field(5, ge=1, le=100, description="返回结果数量")
    threshold: float = Field(0.7, ge=0.0, le=1.0, description="相似度阈值")
    filters: Optional[List[str]] = Field(None, max_items=10, description="搜索过滤器列表")

# 验证请求体
@app.post("/api/v1/search")
async def search_documents(request: SearchRequest):
    """搜索文档接口：使用完整的数据验证规则"""
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
    """上传请求模型：包含自定义验证规则"""
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., min_length=1)

    # 使用@field_validator装饰器定义自定义验证方法
    # "filename" 表示这个验证器是用来验证filename字段的
    # cls参数是类本身（Pydantic的要求）
    # v参数是字段的值
    @field_validator("filename")
    def filename_must_contain_dot(cls, v):
        """自定义验证：文件名必须包含点号（即必须有扩展名）"""
        # 检查文件名是否包含点号
        if "." not in v:
            # 如果验证失败，抛出ValueError异常
            # FastAPI会捕获这个异常，并返回422状态码和清晰的错误信息
            raise ValueError("文件名必须包含扩展名（即必须有点号）")
        # 如果验证通过，返回原始值（或修改后的值）
        return v

    # 第二个自定义验证器，验证content_type字段
    @field_validator("content_type")
    def content_type_must_be_valid(cls, v):
        """自定义验证：内容类型必须是支持的格式"""
        # 定义支持的文件类型列表
        valid_content_types = ["application/pdf", "application/msword", "text/plain"]
        # 检查v是否在支持的列表中
        if v not in valid_content_types:
            raise ValueError(f"不支持的文件类型。支持的类型：{valid_content_types}")
        return v
```

### 3.3 错误处理

#### 3.3.1 基本错误处理
```python
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/api/v1/documents/{document_id}")
async def get_document(document_id: str):
    """根据ID获取文档接口：包含错误处理逻辑"""
    # 模拟文档不存在的情况
    if document_id != "valid-id":
        # 抛出HTTPException异常
        # 参数说明：
        # - status_code: HTTP状态码（404表示资源未找到）
        # - detail: 错误详情信息，会返回给客户端
        # - headers: 可选的响应头
        raise HTTPException(
            status_code=404,
            detail=f"ID为 '{document_id}' 的文档未找到",
            headers={"X-Error": "DocumentNotFound"}
        )
    # 如果文档存在，正常返回
    return {"document_id": document_id, "content": "Document content"}
```

#### 3.3.2 自定义异常
```python
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI()

# 使用@app.exception_handler()装饰器自定义异常处理器
# StarletteHTTPException是FastAPI内部HTTP异常的基类
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    """自定义HTTP异常处理器：统一处理所有HTTP异常"""
    # 返回自定义格式的JSON响应
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "code": exc.status_code}
    )

# 自定义请求验证异常处理器
# RequestValidationError是Pydantic数据验证失败时抛出的异常
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """自定义验证异常处理器：统一处理数据验证失败的情况"""
    return JSONResponse(
        status_code=422,  # 422状态码表示请求格式正确，但语义错误
        content={"error": "数据验证失败", "details": exc.errors()}
    )
```

---

## 4. 依赖注入

### 4.1 基本依赖注入

#### 4.1.1 定义依赖
```python
from fastapi import FastAPI, Depends

app = FastAPI()

# 定义依赖函数
# 依赖函数的作用：在路由函数执行前先执行，做一些前置工作
# 比如：验证用户身份、连接数据库、获取配置等
# Depends()表示这个函数本身也可以作为依赖使用
def get_api_key(api_key: str = Depends()):
    """依赖函数：验证API密钥是否有效"""
    # 简单验证API密钥是否正确
    if api_key != "secret-key":
        # 如果验证失败，抛出401未授权异常
        raise HTTPException(status_code=401, detail="API密钥无效")
    # 如果验证通过，返回API密钥
    return api_key

# 使用依赖函数保护路由
# Depends(get_api_key) 告诉FastAPI：
# "在执行protected_route函数之前，先执行get_api_key函数"
# "把get_api_key的返回值赋值给api_key参数"
@app.get("/api/v1/protected")
async def protected_route(api_key: str = Depends(get_api_key)):
    """受保护的接口：只有提供正确API密钥才能访问"""
    return {"message": "访问成功", "api_key": api_key}
```

#### 4.1.2 类依赖
```python
from fastapi import FastAPI, Depends
from typing import Optional

app = FastAPI()

# 定义数据库类，模拟数据库连接和操作
class Database:
    """数据库类：模拟数据库连接和操作"""
    def __init__(self, db_url: str):
        # 初始化方法：接收数据库连接地址
        self.db_url = db_url
        self.connection = None
    
    def connect(self):
        """连接数据库"""
        self.connection = f"已连接到数据库：{self.db_url}"
        return self.connection
    
    def disconnect(self):
        """断开数据库连接"""
        self.connection = None

# 定义依赖函数，使用yield关键字
# yield的作用：
# 1. yield之前的代码在路由函数执行前执行（获取资源）
# 2. yield之后的代码在路由函数执行后执行（释放资源）
# 3. yield返回的值会传递给路由函数
def get_database(db_url: str = "postgresql://localhost:5432/carabot"):
    """依赖函数：创建并管理数据库连接"""
    # 第一步：创建Database实例并连接数据库
    db = Database(db_url)
    db.connect()
    try:
        # 第二步：yield返回db实例，让路由函数使用
        yield db
    finally:
        # 第三步：无论路由函数执行成功还是失败，都执行这里的代码
        # 确保数据库连接被正确关闭
        db.disconnect()

# 使用数据库依赖
@app.get("/api/v1/db-status")
async def db_status(db: Database = Depends(get_database)):
    """数据库状态接口：返回数据库连接状态"""
    return {"db_url": db.db_url, "connection_status": db.connection}
```

### 4.2 依赖链

```python
from fastapi import FastAPI, Depends, HTTPException

app = FastAPI()

# 第一个依赖：验证API密钥
def get_api_key(api_key: str = Depends()):
    """第一层依赖：验证API密钥"""
    if api_key != "secret-key":
        raise HTTPException(status_code=401, detail="API密钥无效")
    return api_key

# 第二个依赖：依赖于get_api_key
# Depends(get_api_key) 表示这个函数依赖于get_api_key的返回值
# FastAPI会先执行get_api_key，然后把返回值传给get_user
def get_user(api_key: str = Depends(get_api_key)):
    """第二层依赖：根据API密钥获取用户信息"""
    # 模拟从数据库查询用户
    user = {"id": 1, "name": "John Doe", "api_key": api_key}
    return user

# 路由依赖于get_user，形成依赖链
# 完整执行顺序：
# 1. 执行get_api_key（最底层依赖）
# 2. 把get_api_key的返回值传给get_user
# 3. 执行get_user
# 4. 把get_user的返回值传给user_profile
# 5. 执行user_profile
@app.get("/api/v1/user-profile")
async def user_profile(user: dict = Depends(get_user)):
    """用户信息接口：获取当前登录用户的信息"""
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

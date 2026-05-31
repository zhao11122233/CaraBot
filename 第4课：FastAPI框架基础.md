# 第4课：FastAPI框架基础 - 循序渐进学习指南

## 📚 学习路径

按照知识点顺序，我们将一步步学习6个核心知识点：

1. **知识点1**：基本接口（GET、POST、PUT、DELETE）
2. **知识点2**：数据验证（路径参数、查询参数、请求体）
3. **知识点3**：响应模型
4. **知识点4**：依赖注入
5. **知识点5**：错误处理
6. **知识点6**：对比Spring Boot

---

## 知识点1：基本接口（GET、POST、PUT、DELETE）

### 一、基本接口是什么？（大白话）

接口就是：前端访问某个 URL，后端给它返回数据。

- **GET** - 拿数据（查询用户列表、查看详情）
- **POST** - 建数据（注册用户、上传文件）
- **PUT** - 改数据（修改用户信息）
- **DELETE** - 删数据（删除用户）

没有接口时：前后端没法通信。

有了接口：前端访问 `http://localhost:8000/users`，后端返回用户列表。

一句话：接口是前后端通信的桥梁。

### 二、核心：@app.get() 装饰器

语法：

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
def 函数名():
    return 返回值
```

`@app.get("/users")` 告诉 FastAPI：
- 当有人用 **GET** 方法访问 `/users` 时
- 自动调用这个函数
- 把返回值转成 JSON 发给前端

### 三、最简单例子（一看就懂）

```python
from fastapi import FastAPI

app = FastAPI()

# 1. GET：获取用户列表
@app.get("/users")
def get_users():
    return {
        "message": "获取成功",
        "data": [
            {"id": 1, "name": "张三"},
            {"id": 2, "name": "李四"}
        ]
    }

# 2. GET：获取单个用户（带路径参数）
@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {
        "message": "获取成功",
        "data": {"id": user_id, "name": "用户" + str(user_id)}
    }

# 3. POST：创建用户
@app.post("/users")
def create_user(name: str, email: str):
    return {
        "message": "创建成功",
        "data": {"name": name, "email": email}
    }

# 4. PUT：修改用户
@app.put("/users/{user_id}")
def update_user(user_id: int, name: str):
    return {
        "message": "修改成功",
        "data": {"id": user_id, "name": name}
    }

# 5. DELETE：删除用户
@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    return {
        "message": "删除成功",
        "data": {"id": user_id}
    }
```

**发生了什么？**

浏览器访问 `http://localhost:8000/users` 时：
1. FastAPI 检测到是 **GET** 请求，路径是 `/users`
2. 自动调用 `get_users()` 函数
3. 把函数返回的字典转成 JSON
4. 返回给浏览器

你只管写函数逻辑，其他都交给 FastAPI！

### 四、基本接口能做什么？

✅ CRUD 操作（增删改查）
✅ 返回 JSON 数据
✅ 接收 URL 参数（路径参数）
✅ 接收查询参数（?后面的内容）

### 五、一句话总结（必背）

基本接口 = 用 `@app.get/post/put/delete` 装饰器定义 URL 和函数，FastAPI 自动处理请求和响应。

---

## 知识点2：数据验证（路径参数、查询参数、请求体）

### 一、数据验证是什么？（大白话）

**防傻逼** - 保证用户传的数据是对的。

没有数据验证时：
- 用户传 age = "abc"，你的代码报错
- 用户传 name = ""（空字符串），你存进数据库
- 用户传 id = -1，你也正常处理

有了数据验证（FastAPI 自动做）：
- 用户传错数据，直接返回清晰错误
- 不用写一堆 `if` 去判断
- 代码更健壮

一句话：自动检查输入数据，不对就报错。

### 二、核心工具：Path、Query、Pydantic

| 工具 | 用途 | 例子 |
|------|------|------|
| `Path` | 验证路径参数 | `user_id: int = Path(..., ge=1)` |
| `Query` | 验证查询参数 | `skip: int = Query(0, ge=0)` |
| `Pydantic` | 验证请求体 | `class UserCreate(BaseModel)` |

### 三、最常用例子（一看就懂）

#### 1. 验证路径参数

```python
from fastapi import FastAPI, Path

app = FastAPI()

@app.get("/users/{user_id}")
def get_user(user_id: int = Path(..., ge=1, description="用户ID")):
    return {"id": user_id}
```

**`Path` 参数说明：**
- `...` - 必填，不能省略
- `ge=1` - 大于等于 1（greater than or equal）
- `le=100` - 小于等于 100（less than or equal）
- `description` - 描述，会显示在文档里

#### 2. 验证查询参数

```python
from fastapi import FastAPI, Query

@app.get("/users")
def get_users(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(10, ge=1, le=100, description="返回数量")
):
    return {"skip": skip, "limit": limit}
```

**访问示例：**
- `http://localhost:8000/users?skip=0&limit=10` ✓ 正确
- `http://localhost:8000/users?skip=-1` ✗ 报错（ge=0）

#### 3. 验证请求体（最常用！）

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="用户名")
    email: str = Field(..., min_length=5, max_length=100, description="邮箱")
    age: int = Field(None, ge=0, le=150, description="年龄")

@app.post("/users")
def create_user(user: UserCreate):
    return user.model_dump()
```

**`Field` 参数说明：**
- `...` - 必填字段
- `None` - 可选字段
- `min_length` - 最小长度
- `max_length` - 最大长度
- `ge` - 最小值（数字用）
- `le` - 最大值（数字用）

**完整示例代码：**

```python
from fastapi import FastAPI, Path, Query
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI(title="用户管理API", version="2.0.0")

# 请求体模型
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="用户名")
    email: str = Field(..., min_length=5, max_length=100, description="邮箱")
    age: Optional[int] = Field(None, ge=0, le=150, description="年龄")

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    email: Optional[str] = Field(None, min_length=5, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=150)

# 1. GET：用户列表（查询参数验证）
@app.get("/users")
def get_users(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(10, ge=1, le=100, description="返回数量")
):
    return {
        "message": "获取成功",
        "pagination": {"skip": skip, "limit": limit},
        "data": [{"id": 1, "name": "张三"}]
    }

# 2. GET：单个用户（路径参数验证）
@app.get("/users/{user_id}")
def get_user(user_id: int = Path(..., ge=1, description="用户ID")):
    return {
        "message": "获取成功",
        "data": {"id": user_id, "name": "用户" + str(user_id)}
    }

# 3. POST：创建用户（请求体验证）
@app.post("/users")
def create_user(user: UserCreate):
    return {
        "message": "创建成功",
        "data": user.model_dump()
    }

# 4. PUT：修改用户
@app.put("/users/{user_id}")
def update_user(
    user_id: int = Path(..., ge=1),
    user_update: UserUpdate = ...
):
    return {
        "message": "修改成功",
        "data": {"id": user_id, **user_update.model_dump()}
    }

# 5. DELETE：删除用户
@app.delete("/users/{user_id}")
def delete_user(user_id: int = Path(..., ge=1)):
    return {
        "message": "删除成功",
        "data": {"id": user_id}
    }
```

### 四、数据验证能做什么？

✅ 类型检查（字符串、数字、布尔等）
✅ 范围检查（min、max、ge、le）
✅ 长度检查（min_length、max_length）
✅ 必填/可选标记
✅ 自动生成清晰错误信息
✅ 自动显示在 API 文档里

### 五、一句话总结（必背）

数据验证 = 用 `Path/Query/Field` 定义参数规则，FastAPI 自动检查，不符合就报错。

---

## 知识点3：响应模型

### 一、响应模型是什么？（大白话）

**规范输出** - 保证前端收到的数据格式是固定的。

没有响应模型时：
- 同一个接口，今天返回 `{id: 1, name: "张三"}`，明天返回 `{id: 1, username: "张三"}`
- 前端代码总在改
- 容易出 bug

有了响应模型（Pydantic 的 BaseModel）：
- 返回格式固定死
- 字段类型不匹配自动转换
- 文档里清晰显示返回结构

一句话：规定接口返回什么数据、什么类型、什么格式。

### 二、核心：response_model 参数

语法：

```python
from fastapi import FastAPI
from pydantic import BaseModel

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    return {
        "id": user_id,
        "name": "张三",
        "email": "zhangsan@example.com"
    }
```

`response_model=UserResponse` 告诉 FastAPI：
- 把函数返回的数据转成 UserResponse 格式
- 验证类型是否正确
- 只返回模型里定义的字段（多的忽略）

### 三、最常用例子（一看就懂）

#### 1. 定义响应模型

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserResponse(BaseModel):
    user_id: int
    name: str
    email: str
    age: Optional[int] = None
    created_at: datetime
    updated_at: datetime
```

#### 2. 在接口中使用

```python
from fastapi import FastAPI, Path
from typing import List

app = FastAPI()

# 返回单个用户
@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int = Path(..., ge=1)):
    return UserResponse(
        user_id=user_id,
        name="张三",
        email="zhangsan@example.com",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

# 返回用户列表
@app.get("/users", response_model=List[UserResponse])
def get_users():
    return [
        UserResponse(
            user_id=1,
            name="张三",
            email="zhangsan@example.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ),
        UserResponse(
            user_id=2,
            name="李四",
            email="lisi@example.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    ]
```

#### 3. from_attributes 的妙用（从 ORM 对象转）

```python
class UserResponse(BaseModel):
    user_id: int
    name: str
    email: str

    class Config:
        from_attributes = True  # 关键：支持从对象属性获取数据

# 直接返回数据库模型对象
@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    db_user = {"user_id": user_id, "name": "张三", "email": "zhangsan@example.com"}
    return db_user  # FastAPI 自动转成 UserResponse
```

**完整示例代码：**

```python
from fastapi import FastAPI, Path, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

app = FastAPI(title="用户管理API", version="3.0.0")

# 响应模型
class UserResponse(BaseModel):
    user_id: int
    name: str
    email: str
    age: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# 请求体模型
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    email: str = Field(..., min_length=5, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=150)

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    email: Optional[str] = Field(None, min_length=5, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=150)

# 1. GET：用户列表
@app.get("/users", response_model=List[UserResponse])
def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    now = datetime.utcnow()
    return [
        UserResponse(
            user_id=1,
            name="张三",
            email="zhangsan@example.com",
            created_at=now,
            updated_at=now
        )
    ]

# 2. GET：单个用户
@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int = Path(..., ge=1)):
    now = datetime.utcnow()
    return UserResponse(
        user_id=user_id,
        name="用户" + str(user_id),
        email="user" + str(user_id) + "@example.com",
        created_at=now,
        updated_at=now
    )

# 3. POST：创建用户（返回201状态码）
@app.post("/users", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate):
    now = datetime.utcnow()
    return UserResponse(
        user_id=1,
        name=user.name,
        email=user.email,
        age=user.age,
        created_at=now,
        updated_at=now
    )

# 4. PUT：修改用户
@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int = Path(..., ge=1),
    user_update: UserUpdate = ...
):
    now = datetime.utcnow()
    return UserResponse(
        user_id=user_id,
        name=user_update.name or "默认名",
        email=user_update.email or "default@example.com",
        age=user_update.age,
        created_at=now,
        updated_at=now
    )

# 5. DELETE：删除用户（返回204无内容）
@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int = Path(..., ge=1)):
    return None
```

### 四、响应模型能做什么？

✅ 规定返回字段和类型
✅ 自动类型转换
✅ 自动过滤多余字段
✅ 支持从 ORM 对象转换（from_attributes）
✅ 自动生成清晰的文档
✅ 保证不同接口返回格式一致

### 五、一句话总结（必背）

响应模型 = 用 Pydantic 的 BaseModel 定义返回格式，用 `response_model` 参数指定，FastAPI 自动转换和验证。

---

## 知识点4：依赖注入

### 一、依赖注入是什么？（大白话）

你只说 "我需要什么"，框架帮你造好、传进来。

**没有依赖注入时：**
每个接口都要自己写：连接数据库、校验 token、取公共参数……
代码重复、改一处要改十处。

**有了依赖注入（FastAPI 的 Depends）：**
公共逻辑只写一次，做成 "依赖函数"。
接口函数声明需要它，FastAPI 自动执行它、把结果送进来。

一句话：复用代码、解耦、少写重复逻辑。

### 二、核心：Depends()

语法：

```python
from fastapi import Depends

Depends(函数名) 表示：这个参数的值，来自这个函数的返回值。
```

### 三、最简单例子（一看就懂）

#### 1. 定义一个 "公共参数依赖"

```python
from fastapi import FastAPI, Depends

app = FastAPI()

# 公共逻辑：提取查询参数
def common_params(q: str = None, skip: int = 0, limit: int = 10):
    return {"q": q, "skip": skip, "limit": limit}
```

#### 2. 接口里声明要这个依赖

```python
@app.get("/items/")
def read_items(commons: dict = Depends(common_params)):
    return {"msg": "商品列表", **commons}

@app.get("/users/")
def read_users(commons: dict = Depends(common_params)):
    return {"msg": "用户列表", **commons}
```

**发生了什么？**

请求来的时候：
1. FastAPI 先调用 `common_params()`，解析 q/skip/limit
2. 把返回的字典自动传给 `read_items` 或 `read_users` 的 commons 参数
3. 你直接用，不用自己解析参数

### 四、真实项目最常用：数据库会话

```python
from fastapi import Depends

# 模拟数据库类
class MockDatabase:
    def __init__(self):
        self.users = {}
        self.next_id = 1
    
    def get_user(self, user_id: int):
        return self.users.get(user_id)
    
    def create_user(self, user_data: dict):
        user_id = self.next_id
        self.users[user_id] = user_data
        self.next_id += 1
        return user_data
    
    # ... 其他方法

# 依赖函数：管理数据库连接
def get_db():
    print("✅ 数据库连接成功")
    db = MockDatabase()
    try:
        yield db  # 把 db 传给接口
    finally:
        print("🔚 数据库连接关闭")

# 接口声明需要 db
@app.get("/users/")
def get_users(db: MockDatabase = Depends(get_db)):
    users = list(db.users.values())
    return users
```

`get_db()` 负责：
1. 创建连接
2. 用 `yield` 返回会话给接口
3. 请求结束后自动关闭连接

所有接口共用这一个逻辑，不用每个接口都写。

### 五、嵌套依赖（常用在认证）

依赖里还能依赖别的依赖：

```python
from fastapi import HTTPException

# 1. 数据库依赖
def get_db():
    print("连接数据库")
    yield "db_conn"
    print("关闭数据库")

# 2. 认证（依赖数据库）
def auth_user(db = Depends(get_db)):
    print("校验用户")
    return {"user": "张三", "role": "admin"}

# 3. 权限（依赖认证）
def check_permission(user = Depends(auth_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="无权限")
    return user

# 接口只需要声明最终依赖
@app.get("/admin/data")
def admin_data(user = Depends(check_permission)):
    return {"secret": "数据", "user": user}
```

**请求流程：**
1. 执行 `get_db()` → 拿到 db
2. 执行 `auth_user(db)` → 拿到 user
3. 执行 `check_permission(user)` → 校验权限
4. 传给接口函数

自动按顺序执行，层层注入！

### 六、完整示例代码

```python
from fastapi import FastAPI, Path, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

app = FastAPI(title="用户管理API", version="4.0.0")

# 模拟数据库类
class MockDatabase:
    def __init__(self):
        self.users = {}
        self.next_id = 1
    
    def get_user(self, user_id: int):
        return self.users.get(user_id)
    
    def create_user(self, user_data: dict):
        user_id = self.next_id
        now = datetime.utcnow()
        user = {
            "user_id": user_id,
            **user_data,
            "created_at": now,
            "updated_at": now
        }
        self.users[user_id] = user
        self.next_id += 1
        return user
    
    def update_user(self, user_id: int, user_data: dict):
        if user_id not in self.users:
            return None
        user = self.users[user_id]
        user.update(user_data)
        user["updated_at"] = datetime.utcnow()
        return user
    
    def delete_user(self, user_id: int):
        if user_id in self.users:
            del self.users[user_id]
            return True
        return False
    
    def list_users(self, skip: int = 0, limit: int = 10):
        users = list(self.users.values())
        return users[skip: skip + limit]

# 依赖函数：获取数据库实例
def get_db():
    db = MockDatabase()
    # 预置一些测试数据
    db.create_user({"name": "张三", "email": "zhangsan@example.com", "age": 25})
    db.create_user({"name": "李四", "email": "lisi@example.com", "age": 30})
    yield db

# 响应模型
class UserResponse(BaseModel):
    user_id: int
    name: str
    email: str
    age: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# 请求体模型
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    email: str = Field(..., min_length=5, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=150)

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    email: Optional[str] = Field(None, min_length=5, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=150)

# 1. GET：用户列表
@app.get("/users", response_model=List[UserResponse])
def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: MockDatabase = Depends(get_db)
):
    users = db.list_users(skip=skip, limit=limit)
    return [UserResponse(**user) for user in users]

# 2. GET：单个用户
@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int = Path(..., ge=1),
    db: MockDatabase = Depends(get_db)
):
    user = db.get_user(user_id)
    if user:
        return UserResponse(**user)
    return UserResponse(
        user_id=user_id,
        name="未知用户",
        email="unknown@example.com",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

# 3. POST：创建用户
@app.post("/users", response_model=UserResponse, status_code=201)
def create_user(
    user: UserCreate,
    db: MockDatabase = Depends(get_db)
):
    user_dict = user.model_dump()
    new_user = db.create_user(user_dict)
    return UserResponse(**new_user)

# 4. PUT：修改用户
@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int = Path(..., ge=1),
    user_update: UserUpdate = ...,
    db: MockDatabase = Depends(get_db)
):
    if not db.get_user(user_id):
        return UserResponse(
            user_id=user_id,
            name="默认用户",
            email="default@example.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    update_data = user_update.model_dump(exclude_unset=True)
    updated_user = db.update_user(user_id, update_data)
    return UserResponse(**updated_user)

# 5. DELETE：删除用户
@app.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int = Path(..., ge=1),
    db: MockDatabase = Depends(get_db)
):
    db.delete_user(user_id)
    return None
```

### 七、依赖注入能做什么？

✅ 公共参数提取（q/skip/limit）
✅ 数据库会话管理
✅ 用户登录认证、token 校验
✅ 权限控制（管理员/普通用户）
✅ 日志、限流、统计
✅ 代码复用、解耦、好维护

### 八、一句话总结（必背）

依赖注入 = 把公共逻辑抽成函数，用 Depends 声明需要它，FastAPI 自动帮你执行并传入结果。

---

## 知识点5：错误处理

### 一、错误处理是什么？（大白话）

出错时，给前端一个**清晰的、人类能看懂的**说法，而不是让程序崩溃。

**没有错误处理时：**
- 用户访问不存在的 id，程序返回一堆看不懂的 traceback
- 前端不知道发生了什么，只能显示 "系统错误"
- 体验很差

**有了错误处理（FastAPI 的 HTTPException）：**
- 用户访问不存在的 id，返回 `{"detail": "用户不存在"}`
- 前端能给用户明确提示
- 专业、友好

一句话：程序出错时，优雅地返回错误信息，而不是崩溃。

### 二、核心：HTTPException

语法：

```python
from fastapi import HTTPException

raise HTTPException(
    status_code=404,        # HTTP 状态码
    detail="用户不存在",     # 错误详情
    headers={"X-Error": "UserNotFound"}  # 可选：自定义响应头
)
```

### 三、最常用例子（一看就懂）

#### 1. 404 Not Found（资源不存在）

```python
from fastapi import FastAPI, Path, HTTPException

app = FastAPI()

@app.get("/users/{user_id}")
def get_user(user_id: int = Path(..., ge=1)):
    # 模拟数据库查询
    user = None  # 假设没查到
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"用户ID {user_id} 不存在"
        )
    
    return {"user": user}
```

#### 2. 403 Forbidden（无权访问）

```python
@app.get("/admin/data")
def get_admin_data(user: dict = Depends(check_permission)):
    if user["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="无权访问该接口"
        )
    return {"secret": "管理员专属数据"}
```

#### 3. 400 Bad Request（请求错误）

```python
@app.post("/users")
def create_user(user: UserCreate):
    # 检查用户名是否重复
    if user.name in ["张三", "李四"]:
        raise HTTPException(
            status_code=400,
            detail="用户名已存在"
        )
    return {"user": user}
```

### 四、常用 HTTP 状态码速查表

| 状态码 | 含义 | 使用场景 |
|--------|------|----------|
| 200 | OK | 成功 |
| 201 | Created | 创建成功（POST用） |
| 204 | No Content | 删除成功，无返回内容 |
| 400 | Bad Request | 请求参数错误 |
| 401 | Unauthorized | 未登录 |
| 403 | Forbidden | 已登录但无权访问 |
| 404 | Not Found | 资源不存在 |
| 422 | Validation Error | 数据验证失败（FastAPI自动返回） |
| 500 | Internal Server Error | 服务器内部错误 |

### 五、完整示例代码

```python
from fastapi import FastAPI, Path, Query, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

app = FastAPI(title="用户管理API", version="5.0.0")

# 模拟数据库类
class MockDatabase:
    def __init__(self):
        self.users = {}
        self.next_id = 1
    
    def get_user(self, user_id: int):
        return self.users.get(user_id)
    
    def create_user(self, user_data: dict):
        user_id = self.next_id
        now = datetime.utcnow()
        user = {
            "user_id": user_id,
            **user_data,
            "created_at": now,
            "updated_at": now
        }
        self.users[user_id] = user
        self.next_id += 1
        return user
    
    def update_user(self, user_id: int, user_data: dict):
        if user_id not in self.users:
            return None
        user = self.users[user_id]
        user.update(user_data)
        user["updated_at"] = datetime.utcnow()
        return user
    
    def delete_user(self, user_id: int):
        if user_id in self.users:
            del self.users[user_id]
            return True
        return False
    
    def list_users(self, skip: int = 0, limit: int = 10):
        users = list(self.users.values())
        return users[skip: skip + limit]

# 依赖函数
def get_db():
    db = MockDatabase()
    db.create_user({"name": "张三", "email": "zhangsan@example.com", "age": 25})
    db.create_user({"name": "李四", "email": "lisi@example.com", "age": 30})
    yield db

# 响应模型
class UserResponse(BaseModel):
    user_id: int
    name: str
    email: str
    age: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# 请求体模型
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    email: str = Field(..., min_length=5, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=150)

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    email: Optional[str] = Field(None, min_length=5, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=150)

# 1. GET：用户列表
@app.get("/users", response_model=List[UserResponse])
def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: MockDatabase = Depends(get_db)
):
    users = db.list_users(skip=skip, limit=limit)
    return [UserResponse(**user) for user in users]

# 2. GET：单个用户（带404错误处理）
@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int = Path(..., ge=1),
    db: MockDatabase = Depends(get_db)
):
    user = db.get_user(user_id)
    if not user:
        # 抛出404错误
        raise HTTPException(
            status_code=404,
            detail=f"用户ID {user_id} 不存在"
        )
    return UserResponse(**user)

# 3. POST：创建用户
@app.post("/users", response_model=UserResponse, status_code=201)
def create_user(
    user: UserCreate,
    db: MockDatabase = Depends(get_db)
):
    new_user = db.create_user(user.model_dump())
    return UserResponse(**new_user)

# 4. PUT：修改用户（带404错误处理）
@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int = Path(..., ge=1),
    user_update: UserUpdate = ...,
    db: MockDatabase = Depends(get_db)
):
    # 检查用户是否存在
    if not db.get_user(user_id):
        raise HTTPException(
            status_code=404,
            detail=f"用户ID {user_id} 不存在，无法更新"
        )
    update_data = user_update.model_dump(exclude_unset=True)
    updated_user = db.update_user(user_id, update_data)
    return UserResponse(**updated_user)

# 5. DELETE：删除用户（带404错误处理）
@app.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int = Path(..., ge=1),
    db: MockDatabase = Depends(get_db)
):
    success = db.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"用户ID {user_id} 不存在，无法删除"
        )
    return None
```

### 六、错误处理能做什么？

✅ 返回清晰的错误信息给前端
✅ 使用标准的 HTTP 状态码
✅ 区分不同错误类型（404、403、400等）
✅ 提升用户体验
✅ 便于前端处理错误
✅ 让程序更健壮，不会轻易崩溃

### 七、一句话总结（必背）

错误处理 = 发现错误时用 `HTTPException` 抛出异常，指定状态码和错误信息，FastAPI 自动返回给前端。

---

## 知识点6：对比Spring Boot

### 一、为什么要对比？（大白话）

技术选型时，知道 FastAPI 和 Spring Boot 的优缺点，帮你选对工具。

| 场景 | 推荐 | 原因 |
|------|------|------|
| 快速原型、小项目 | FastAPI | 开发快、代码少、易上手 |
| 企业级大项目、Java团队 | Spring Boot | 生态全、性能好、稳定 |
| 数据科学、AI项目 | FastAPI | Python生态好、和 Pandas/PyTorch 无缝集成 |

一句话：FastAPI 快且简单，Spring Boot 重但强大，根据场景选。

### 二、详细对比表格

| 特性 | FastAPI | Spring Boot | 说明 |
|------|---------|-------------|------|
| **编程语言** | Python | Java/Kotlin | FastAPI更简洁；Spring Boot更适合企业级大规模应用 |
| **运行方式** | 解释执行，无需编译 | 需要编译成JAR/WAR文件 | FastAPI开发更快；Spring Boot性能更好 |
| **API文档** | 自动生成Swagger UI、ReDoc | 需要配置Springfox/SpringDoc | FastAPI开箱即用，无需额外配置 |
| **数据验证** | 基于Pydantic和类型提示 | 需要@Valid和注解 | FastAPI验证更简洁；Spring Boot需要手动添加注解 |
| **异步支持** | 原生支持async/await | 支持但配置复杂 | FastAPI异步编程更简单直观 |
| **启动时间** | 秒级启动，非常快 | 几秒到十几秒 | FastAPI开发体验更好，迭代更快 |
| **依赖管理** | requirements.txt | pom.xml/build.gradle | Python依赖管理更简单 |
| **学习曲线** | 平缓，容易上手 | 陡峭，概念多 | FastAPI适合新手；Spring Boot需要学的东西多 |
| **性能** | 高 | 很高 | Spring Boot编译后运行更快 |
| **生态** | Python生态全（数据科学、AI） | Java生态全（企业级、微服务） | 各有所长，看团队技术栈 |

### 三、完整示例代码（最终版）

```python
from fastapi import FastAPI, Path, Query, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

app = FastAPI(title="用户管理API", version="6.0.0")

# 模拟数据库类
class MockDatabase:
    def __init__(self):
        self.users = {}
        self.next_id = 1
    
    def get_user(self, user_id: int):
        return self.users.get(user_id)
    
    def create_user(self, user_data: dict):
        user_id = self.next_id
        now = datetime.utcnow()
        user = {
            "user_id": user_id,
            **user_data,
            "created_at": now,
            "updated_at": now
        }
        self.users[user_id] = user
        self.next_id += 1
        return user
    
    def update_user(self, user_id: int, user_data: dict):
        if user_id not in self.users:
            return None
        user = self.users[user_id]
        user.update(user_data)
        user["updated_at"] = datetime.utcnow()
        return user
    
    def delete_user(self, user_id: int):
        if user_id in self.users:
            del self.users[user_id]
            return True
        return False
    
    def list_users(self, skip: int = 0, limit: int = 10):
        users = list(self.users.values())
        return users[skip: skip + limit]

# 依赖函数
def get_db():
    db = MockDatabase()
    db.create_user({"name": "张三", "email": "zhangsan@example.com", "age": 25})
    db.create_user({"name": "李四", "email": "lisi@example.com", "age": 30})
    yield db

# 响应模型
class UserResponse(BaseModel):
    user_id: int
    name: str
    email: str
    age: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# 请求体模型
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    email: str = Field(..., min_length=5, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=150)

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    email: Optional[str] = Field(None, min_length=5, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=150)

# 1. GET：用户列表
@app.get("/users", response_model=List[UserResponse], summary="获取用户列表")
def get_users(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(10, ge=1, le=100, description="返回数量"),
    db: MockDatabase = Depends(get_db)
):
    users = db.list_users(skip=skip, limit=limit)
    return [UserResponse(**user) for user in users]

# 2. GET：单个用户
@app.get("/users/{user_id}", response_model=UserResponse, summary="获取单个用户")
def get_user(
    user_id: int = Path(..., ge=1, description="用户ID"),
    db: MockDatabase = Depends(get_db)
):
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"用户ID {user_id} 不存在"
        )
    return UserResponse(**user)

# 3. POST：创建用户
@app.post("/users", response_model=UserResponse, status_code=201, summary="创建用户")
def create_user(
    user: UserCreate,
    db: MockDatabase = Depends(get_db)
):
    new_user = db.create_user(user.model_dump())
    return UserResponse(**new_user)

# 4. PUT：修改用户
@app.put("/users/{user_id}", response_model=UserResponse, summary="更新用户")
def update_user(
    user_id: int = Path(..., ge=1, description="用户ID"),
    user_update: UserUpdate = ...,
    db: MockDatabase = Depends(get_db)
):
    if not db.get_user(user_id):
        raise HTTPException(
            status_code=404,
            detail=f"用户ID {user_id} 不存在，无法更新"
        )
    update_data = user_update.model_dump(exclude_unset=True)
    updated_user = db.update_user(user_id, update_data)
    return UserResponse(**updated_user)

# 5. DELETE：删除用户
@app.delete("/users/{user_id}", status_code=204, summary="删除用户")
def delete_user(
    user_id: int = Path(..., ge=1, description="用户ID"),
    db: MockDatabase = Depends(get_db)
):
    success = db.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"用户ID {user_id} 不存在，无法删除"
        )
    return None

# 6. 健康检查
@app.get("/health", summary="健康检查")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

# 7. FastAPI vs Spring Boot 对比接口
@app.get("/fastapi-vs-springboot", summary="FastAPI vs Spring Boot 对比")
def compare_frameworks():
    return {
        "comparison": [
            {
                "feature": "编程语言",
                "fastapi": "Python",
                "spring_boot": "Java/Kotlin",
                "description": "FastAPI更简洁；Spring Boot更适合企业级大规模应用"
            },
            {
                "feature": "运行方式",
                "fastapi": "解释执行，无需编译",
                "spring_boot": "需要编译成JAR/WAR文件",
                "description": "FastAPI开发更快；Spring Boot性能更好"
            },
            {
                "feature": "API文档",
                "fastapi": "自动生成Swagger UI、ReDoc",
                "spring_boot": "需要配置Springfox/SpringDoc",
                "description": "FastAPI开箱即用，无需额外配置"
            },
            {
                "feature": "数据验证",
                "fastapi": "基于Pydantic和类型提示",
                "spring_boot": "需要@Valid和注解",
                "description": "FastAPI验证更简洁；Spring Boot需要手动添加注解"
            },
            {
                "feature": "异步支持",
                "fastapi": "原生支持async/await",
                "spring_boot": "支持但配置复杂",
                "description": "FastAPI异步编程更简单直观"
            },
            {
                "feature": "启动时间",
                "fastapi": "秒级启动，非常快",
                "spring_boot": "几秒到十几秒",
                "description": "FastAPI开发体验更好，迭代更快"
            },
            {
                "feature": "依赖管理",
                "fastapi": "requirements.txt",
                "spring_boot": "pom.xml/build.gradle",
                "description": "Python依赖管理更简单"
            }
        ]
    }
```

### 四、一句话总结（必背）

FastAPI vs Spring Boot = FastAPI 快且简单适合快速开发，Spring Boot 重但强大适合企业级，根据团队技术栈和项目规模选。

---

## 📝 作业完成总结

| 作业要求 | 完成情况 | 对应知识点 |
|----------|----------|------------|
| 1. 编写至少3个不同类型的接口 | ✅ | 知识点1 |
| 2. 添加数据验证 | ✅ | 知识点2 |
| 3. 定义响应模型 | ✅ | 知识点3 |
| 4. 实现依赖注入 | ✅ | 知识点4 |
| 5. 添加错误处理 | ✅ | 知识点5 |
| 6. 对比FastAPI与Spring Boot | ✅ | 知识点6 |

## 🚀 运行指南

### 安装依赖

```bash
pip install fastapi uvicorn
```

### 运行指定版本

```bash
# 第1版：基本接口
uvicorn v1_basic_endpoints:app --reload

# 第2版：数据验证
uvicorn v2_data_validation:app --reload

# 第3版：响应模型
uvicorn v3_response_models:app --reload

# 第4版：依赖注入
uvicorn v4_dependency_injection:app --reload

# 第5版：错误处理
uvicorn v5_error_handling:app --reload

# 第6版：完整最终版（推荐）
uvicorn v6_complete_final:app --reload
```

### 访问文档

- Swagger UI（可交互式文档）：http://localhost:8000/docs
- ReDoc（更美观的文档）：http://localhost:8000/redoc

## 💡 6个知识点一句话总结（必背！）

1. **基本接口** = 用 `@app.get/post/put/delete` 装饰器定义 URL 和函数，FastAPI 自动处理请求和响应。
2. **数据验证** = 用 `Path/Query/Field` 定义参数规则，FastAPI 自动检查，不符合就报错。
3. **响应模型** = 用 Pydantic 的 BaseModel 定义返回格式，用 `response_model` 参数指定，FastAPI 自动转换和验证。
4. **依赖注入** = 把公共逻辑抽成函数，用 Depends 声明需要它，FastAPI 自动帮你执行并传入结果。
5. **错误处理** = 发现错误时用 `HTTPException` 抛出异常，指定状态码和错误信息，FastAPI 自动返回给前端。
6. **FastAPI vs Spring Boot** = FastAPI 快且简单适合快速开发，Spring Boot 重但强大适合企业级，根据团队技术栈和项目规模选。

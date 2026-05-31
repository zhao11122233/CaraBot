"""
v6：完整最终版
学习知识点6（对比Spring Boot）
"""

from fastapi import FastAPI, Path, Query, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# 创建 FastAPI 应用
app = FastAPI(title="用户管理API", version="6.0.0")


# 模拟数据库类
class MockDatabase:
    def __init__(self):
        self.users = {}  # 存储用户数据
        self.next_id = 1  # 下一个用户ID

    # 根据ID获取用户
    def get_user(self, user_id: int):
        return self.users.get(user_id)

    # 创建新用户
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

    # 更新用户
    def update_user(self, user_id: int, user_data: dict):
        if user_id not in self.users:
            return None
        user = self.users[user_id]
        user.update(user_data)
        user["updated_at"] = datetime.utcnow()
        return user

    # 删除用户
    def delete_user(self, user_id: int):
        if user_id in self.users:
            del self.users[user_id]
            return True
        return False

    # 获取用户列表（分页）
    def list_users(self, skip: int = 0, limit: int = 10):
        users = list(self.users.values())
        return users[skip: skip + limit]


# 依赖注入函数：获取数据库连接
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


# 请求体模型：创建用户
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    email: str = Field(..., min_length=5, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=150)


# 请求体模型：更新用户
class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    email: Optional[str] = Field(None, min_length=5, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=150)


# GET：获取用户列表（summary：接口描述，显示在文档中）
@app.get("/users", response_model=List[UserResponse], summary="获取用户列表")
async def get_users(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(10, ge=1, le=100, description="返回数量"),
    db: MockDatabase = Depends(get_db)
):
    users = db.list_users(skip=skip, limit=limit)
    return [UserResponse(**user) for user in users]


# GET：获取单个用户
@app.get("/users/{user_id}", response_model=UserResponse, summary="获取单个用户")
async def get_user(
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


# POST：创建用户
@app.post("/users", response_model=UserResponse, status_code=201, summary="创建用户")
async def create_user(
    user: UserCreate,
    db: MockDatabase = Depends(get_db)
):
    new_user = db.create_user(user.model_dump())
    return UserResponse(**new_user)


# PUT：修改用户
@app.put("/users/{user_id}", response_model=UserResponse, summary="更新用户")
async def update_user(
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


# DELETE：删除用户
@app.delete("/users/{user_id}", status_code=204, summary="删除用户")
async def delete_user(
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


# 健康检查接口（生产环境常用）
@app.get("/health", summary="健康检查")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


# FastAPI vs Spring Boot 对比接口（学习用）
@app.get("/fastapi-vs-springboot", summary="FastAPI vs Spring Boot 对比")
async def compare_frameworks():
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

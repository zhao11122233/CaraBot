"""
v3：响应模型
学习知识点3
"""

from fastapi import FastAPI, Path, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# 创建 FastAPI 应用
app = FastAPI(title="用户管理API", version="3.0.0")


# 响应模型：规定返回给前端的数据格式
class UserResponse(BaseModel):
    user_id: int  # 用户ID
    name: str  # 用户名
    email: str  # 邮箱
    age: Optional[int] = None  # 年龄（可选）
    created_at: datetime  # 创建时间
    updated_at: datetime  # 更新时间

    class Config:
        from_attributes = True  # 支持从对象属性转换


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


# GET：获取用户列表（response_model：规定返回格式）
@app.get("/users", response_model=List[UserResponse])
async def get_users(
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


# GET：获取单个用户
@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int = Path(..., ge=1)):
    now = datetime.utcnow()
    return UserResponse(
        user_id=user_id,
        name="用户" + str(user_id),
        email="user" + str(user_id) + "@example.com",
        created_at=now,
        updated_at=now
    )


# POST：创建用户（status_code=201：创建成功）
@app.post("/users", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate):
    now = datetime.utcnow()
    return UserResponse(
        user_id=1,
        name=user.name,
        email=user.email,
        age=user.age,
        created_at=now,
        updated_at=now
    )


# PUT：修改用户
@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int = Path(..., ge=1),
    user_update: UserUpdate = ...
):
    now = datetime.utcnow()
    return UserResponse(
        user_id=user_id,
        name=user_update.name or "默认用户",
        email=user_update.email or "default@example.com",
        age=user_update.age,
        created_at=now,
        updated_at=now
    )


# DELETE：删除用户（status_code=204：无内容返回）
@app.delete("/users/{user_id}", status_code=204)
async def delete_user(user_id: int = Path(..., ge=1)):
    return None

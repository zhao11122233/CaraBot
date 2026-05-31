"""
v2：数据验证（路径参数、查询参数、请求体）
学习知识点2
"""

from fastapi import FastAPI, Path, Query
from pydantic import BaseModel, Field
from typing import Optional

# 创建 FastAPI 应用
app = FastAPI(title="用户管理API", version="2.0.0")


# 请求体模型：创建用户（用 Field 做数据验证）
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="用户名")  # 必填，2-50字符
    email: str = Field(..., min_length=5, max_length=100, description="邮箱")  # 必填，5-100字符
    age: Optional[int] = Field(None, ge=0, le=150, description="年龄")  # 可选，0-150岁


# 请求体模型：更新用户（所有字段都是可选的）
class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    email: Optional[str] = Field(None, min_length=5, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=150)


# GET：获取用户列表（Query：查询参数验证）
@app.get("/users")
async def get_users(
    skip: int = Query(0, ge=0, description="跳过数量"),  # 最小值0
    limit: int = Query(10, ge=1, le=100, description="返回数量")  # 1-100
):
    return {
        "message": "获取成功",
        "pagination": {"skip": skip, "limit": limit},
        "data": [{"id": 1, "name": "张三"}]
    }


# GET：获取单个用户（Path：路径参数验证）
@app.get("/users/{user_id}")
async def get_user(user_id: int = Path(..., ge=1, description="用户ID")):  # 最小值1
    return {
        "message": "获取成功",
        "data": {"id": user_id, "name": "用户" + str(user_id)}
    }


# POST：创建用户（用 Pydantic 模型验证请求体）
@app.post("/users")
async def create_user(user: UserCreate):
    return {
        "message": "创建成功",
        "data": user.model_dump()
    }


# PUT：修改用户
@app.put("/users/{user_id}")
async def update_user(
    user_id: int = Path(..., ge=1),
    user_update: UserUpdate = ...
):
    return {
        "message": "修改成功",
        "data": {"id": user_id, **user_update.model_dump()}
    }


# DELETE：删除用户
@app.delete("/users/{user_id}")
async def delete_user(user_id: int = Path(..., ge=1)):
    return {
        "message": "删除成功",
        "data": {"id": user_id}
    }

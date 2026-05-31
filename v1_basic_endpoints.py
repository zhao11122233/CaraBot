"""
v1：基本接口（GET、POST、PUT、DELETE）
学习知识点1
"""

from fastapi import FastAPI

# 创建 FastAPI 应用
app = FastAPI(title="用户管理API", version="1.0.0")


# GET：获取用户列表
@app.get("/users")
async def get_users():
    return {
        "message": "获取成功",
        "data": [
            {"id": 1, "name": "张三"},
            {"id": 2, "name": "李四"}
        ]
    }


# GET：获取单个用户（路径参数）
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    return {
        "message": "获取成功",
        "data": {"id": user_id, "name": "用户" + str(user_id)}
    }


# POST：创建用户（查询参数）
@app.post("/users")
async def create_user(name: str, email: str):
    return {
        "message": "创建成功",
        "data": {"name": name, "email": email}
    }


# PUT：修改用户
@app.put("/users/{user_id}")
async def update_user(user_id: int, name: str):
    return {
        "message": "修改成功",
        "data": {"id": user_id, "name": name}
    }


# DELETE：删除用户
@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    return {
        "message": "删除成功",
        "data": {"id": user_id}
    }

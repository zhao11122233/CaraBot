"""
v4：依赖注入
学习知识点4
"""

from fastapi import FastAPI, Path, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

app = FastAPI(title="用户管理API", version="4.0.0")


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


def get_db():
    db = MockDatabase()
    db.create_user({"name": "张三", "email": "zhangsan@example.com", "age": 25})
    db.create_user({"name": "李四", "email": "lisi@example.com", "age": 30})
    yield db


class UserResponse(BaseModel):
    user_id: int
    name: str
    email: str
    age: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    email: str = Field(..., min_length=5, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=150)


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    email: Optional[str] = Field(None, min_length=5, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=150)


@app.get("/users", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: MockDatabase = Depends(get_db)
):
    users = db.list_users(skip=skip, limit=limit)
    return [UserResponse(**user) for user in users]


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
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


@app.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    user: UserCreate,
    db: MockDatabase = Depends(get_db)
):
    user_dict = user.model_dump()
    new_user = db.create_user(user_dict)
    return UserResponse(**new_user)


@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
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


@app.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: int = Path(..., ge=1),
    db: MockDatabase = Depends(get_db)
):
    db.delete_user(user_id)
    return None

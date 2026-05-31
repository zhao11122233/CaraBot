"""
第4课：FastAPI框架基础 - 课后作业模板

作业要求：
1. 编写至少 3 个不同类型的接口（GET、POST、PUT、DELETE）
2. 为接口添加数据验证，包括路径参数、查询参数和请求体
3. 为接口定义响应模型，确保返回的数据格式正确
4. 实现一个简单的依赖注入，比如数据库连接
5. 为接口添加错误处理，返回清晰的错误信息
6. 对比 FastAPI 与 Spring Boot 的差异，列出至少 5 个不同点

运行方式：
uvicorn 第4课作业答案:app --reload

访问文档：
http://localhost:8000/docs  (Swagger UI)
http://localhost:8000/redoc (ReDoc)
"""

from fastapi import FastAPI, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime

# ============================================
# 在这里开始编写你的作业答案

app=FastAPI(title="CaraBot API",version="1.0.0")

#统一响应模型
class ResponseModel(BaseModel):
    code:int
    msg:str
    data:Optional[dict]=None
#1.get接口（查询路径参数校验）
@app.get("/user/{user_id}",response_model=ResponseModel)
async def get_user(
    user_id:int=Path(...,ge=1,description="ID>=1")
):
    return ResponseModel(code=200,msg="成功",data={"user_id":user_id})

#2.post接口（创建请求体加强校验）
class UserCreate(BaseModel):
    name:str=Field(...,min_length=2,max_length=20,pattern=r"^[a-zA-Z0-9_]+$")
    age:int=Field(...,ge=0,le=120)


@app.post("/user",response_model=ResponseModel)
async def create_user(user:UserCreate):
    #自定义业务校验示例
    if user.age<18:
        raise HTTPException(status_code=400,detail="用户必须年满18岁")
    return ResponseModel(code=200,msg="用户创建成功",data=user.dict())

#3.put接口（更新）
@app.put("/user/{user_id}",response_model=ResponseModel)
async def update_user(
    user_id:int=Path(...,ge=1),
    status:str=Query("normal",max_length=10,pattern=r"^[a-z]+$")
    ):
    return ResponseModel(code=200,msg=f"用户{user_id}状态更新为{status}",data={"user_id":user_id,"status":status})

#4.delete接口（删除）
@app.delete("/user/{user_id}",response_model=ResponseModel)
async def delete_user(
    user_id:int=Path(...,ge=1)
    ):
    return ResponseModel(code=200,msg=f"用户{user_id}删除成功")
# ============================================


# 提示：你可以参考课程文档中的代码示例
# 建议先完成一个功能，测试通过后再继续下一个

# ============================================
# 1. 数据模型定义（包含数据验证）
# ============================================

# 在这里定义你的数据模型（继承BaseModel）
# 示例：
# class YourModel(BaseModel):
#     field1: str = Field(..., min_length=1, description="字段描述")
#     field2: int = Field(0, ge=0, description="字段描述")

# ============================================
# 2. 依赖注入
# ============================================

# 在这里实现你的依赖注入
# 示例：
# def get_dependency():
#     # 获取资源
#     yield resource
#     # 释放资源

# ============================================
# 3. 创建FastAPI应用
# ============================================

app = FastAPI(
    title="第4课作业",
    description="在这里描述你的API",
    version="1.0.0"
)

# ============================================
# 4. 实现各种类型的接口
# ============================================

# 在这里编写你的接口
# 建议至少实现3种不同类型的接口：GET、POST、PUT、DELETE

# ============================================
# 5. 健康检查接口
# ============================================

@app.get("/health", summary="健康检查")
async def health_check():
    """
    健康检查接口，用于确认服务是否正常运行
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

# ============================================
# 6. 对比 FastAPI 与 Spring Boot
# ============================================

# 在这里对比 FastAPI 与 Spring Boot 的差异
# 建议列出至少5个不同点

# ============================================
# 运行服务
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

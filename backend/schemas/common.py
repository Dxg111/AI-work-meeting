"""
通用 Schemas
"""
from pydantic import BaseModel
from typing import Optional, List, Any


class PaginatedResponse(BaseModel):
    """分页响应模型"""
    list: List[Any]
    total: int
    page: int
    page_size: int


class SuccessResponse(BaseModel):
    """成功响应模型"""
    code: int = 200
    message: str = "操作成功"
    data: Optional[Any] = None

"""
统一响应格式模块
"""
from typing import Any, Optional
from fastapi.responses import JSONResponse


class APIResponse:
    """统一 API 响应格式"""

    @staticmethod
    def success(data: Any = None, message: str = "操作成功", code: int = 200) -> dict:
        """成功响应"""
        return {
            "code": code,
            "message": message,
            "data": data
        }

    @staticmethod
    def error(message: str = "操作失败", code: int = 400, data: Any = None) -> dict:
        """错误响应"""
        return {
            "code": code,
            "message": message,
            "data": data
        }

    @staticmethod
    def paginated(items: list, total: int, page: int, page_size: int, message: str = "查询成功") -> dict:
        """分页响应"""
        return {
            "code": 200,
            "message": message,
            "data": {
                "list": items,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        }

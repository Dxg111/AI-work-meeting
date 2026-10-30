"""
统一响应格式模块
"""
from typing import Any, Optional
from fastapi.responses import JSONResponse


def success(data: Any = None, message: str = "操作成功", code: int = 200) -> dict:
    """成功响应"""
    return {
        "code": code,
        "message": message,
        "data": data
    }


def error(message: str = "操作失败", code: int = 400, data: Any = None) -> dict:
    """错误响应"""
    return {
        "code": code,
        "message": message,
        "data": data
    }


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


class APIResponse:
    """统一 API 响应格式（兼容类方式调用）"""

    @staticmethod
    def success(data: Any = None, message: str = "操作成功", code: int = 200) -> dict:
        return success(data, message, code)

    @staticmethod
    def error(message: str = "操作失败", code: int = 400, data: Any = None) -> dict:
        return error(message, code, data)

    @staticmethod
    def paginated(items: list, total: int, page: int, page_size: int, message: str = "查询成功") -> dict:
        return paginated(items, total, page, page_size, message)

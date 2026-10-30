"""
认证相关 Schemas
"""
import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., min_length=1, max_length=128, description="密码")


class UserOut(BaseModel):
    """用户信息输出"""
    user_id: int
    username: str
    nickname: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str
    dept_id: Optional[int] = None
    dept_name: Optional[str] = None
    is_active: bool
    must_change_password: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """登录响应"""
    token: str
    token_type: str = "bearer"
    user: UserOut


class ProfileUpdateRequest(BaseModel):
    """个人资料修改"""
    nickname: Optional[str] = Field(None, max_length=100, description="昵称")
    email: Optional[str] = Field(None, max_length=100, description="邮箱")

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: Optional[str]) -> Optional[str]:
        if value is None or value.strip() == "":
            return None
        value = value.strip()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value):
            raise ValueError("邮箱格式不正确")
        return value


class ChangePasswordRequest(BaseModel):
    """修改密码"""
    old_password: str = Field(..., min_length=1, max_length=128, description="原密码")
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")

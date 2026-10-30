"""
组织管理（部门 / 用户）Schemas
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class DeptCreate(BaseModel):
    dept_name: str = Field(..., min_length=1, max_length=100, description="部门名称")
    dept_desc: Optional[str] = Field(None, max_length=500, description="部门描述")


class DeptUpdate(DeptCreate):
    pass


class DeptOut(BaseModel):
    dept_id: int
    dept_name: str
    dept_desc: Optional[str] = None
    user_count: int = 0
    created_at: datetime


class DeptOption(BaseModel):
    dept_id: int
    dept_name: str


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="登录名")
    password: str = Field(..., min_length=6, max_length=128, description="初始密码")
    nickname: Optional[str] = Field(None, max_length=100, description="昵称")
    dept_id: Optional[int] = Field(None, description="所属部门")
    role: Literal["super_admin", "normal_user"] = Field("normal_user", description="角色")


class UserUpdate(BaseModel):
    nickname: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=100)
    dept_id: Optional[int] = None
    role: Optional[Literal["super_admin", "normal_user"]] = None
    is_active: Optional[bool] = None


class UserStatusRequest(BaseModel):
    is_active: bool


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=6, max_length=128)


class OrgUserOut(BaseModel):
    user_id: int
    username: str
    nickname: Optional[str] = None
    email: Optional[str] = None
    role: str
    dept_id: Optional[int] = None
    dept_name: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

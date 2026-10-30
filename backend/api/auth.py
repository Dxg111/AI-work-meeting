"""
认证 API 路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.exceptions import ForbiddenException, UnauthorizedException
from core.response import success
from core.security import create_access_token, get_current_user
from models.user import User
from schemas.auth import LoginRequest, UserOut
from services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["认证"])


def _user_payload(user: User) -> dict:
    """将用户模型转换为可 JSON 序列化的字典"""
    return UserOut.model_validate(user).model_dump(mode="json")


@router.post("/login", summary="用户登录")
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    用户名 + 密码登录

    - 用户名或密码错误：401
    - 账号被禁用：403
    - 成功：返回 JWT token 与用户信息
    """
    user = await auth_service.authenticate_user(payload.username, payload.password, db)

    if not user:
        raise UnauthorizedException("用户名或密码错误")

    if not user.is_active:
        raise ForbiddenException("账号已被禁用，请联系管理员")

    token = create_access_token({
        "user_id": user.user_id,
        "username": user.username,
        "role": user.role,
        "dept_id": user.dept_id,
    })

    return success(
        data={
            "token": token,
            "token_type": "bearer",
            "user": _user_payload(user),
        },
        message="登录成功",
    )


@router.get("/me", summary="获取当前登录用户")
async def get_me(current_user: User = Depends(get_current_user)):
    """返回当前 token 对应的用户信息"""
    return success(data=_user_payload(current_user))


@router.post("/logout", summary="退出登录")
async def logout(current_user: User = Depends(get_current_user)):
    """
    退出登录

    JWT 为无状态令牌，服务端不维护会话；前端清除本地 token 即可。
    """
    return success(message="退出成功")

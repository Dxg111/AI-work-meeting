"""
认证与个人中心 API 路由
"""
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.exceptions import ForbiddenException, UnauthorizedException
from core.response import success
from core.security import create_access_token, get_current_user
from models.dept import Department
from models.user import User
from schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    ProfileUpdateRequest,
    UserOut,
)
from services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["认证"])


async def _user_payload(user: User, db: AsyncSession) -> dict:
    """将用户模型转换为可 JSON 序列化的字典（含部门名称）"""
    data = UserOut.model_validate(user).model_dump(mode="json")
    dept = await db.get(Department, user.dept_id) if user.dept_id else None
    data["dept_name"] = dept.dept_name if dept else None
    return data


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
            "user": await _user_payload(user, db),
        },
        message="登录成功",
    )


@router.get("/me", summary="获取当前登录用户")
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """返回当前 token 对应的用户信息（含所属部门）"""
    return success(data=await _user_payload(current_user, db))


@router.put("/profile", summary="修改个人资料")
async def update_profile(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """修改昵称、邮箱"""
    user = await auth_service.update_profile(current_user, payload, db)
    return success(data=await _user_payload(user, db), message="资料更新成功")


@router.put("/password", summary="修改本人密码")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """校验原密码后修改新密码"""
    await auth_service.change_password(
        current_user,
        payload.old_password,
        payload.new_password,
        db,
    )
    return success(message="密码修改成功")


@router.post("/avatar", summary="上传头像")
async def upload_avatar(
    file: UploadFile = File(..., description="头像图片"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上传头像，保存到 uploads/avatars，并更新用户头像路径"""
    user = await auth_service.update_avatar(current_user, file, db)
    return success(
        data={"avatar_url": user.avatar_url},
        message="头像上传成功",
    )


@router.post("/logout", summary="退出登录")
async def logout(current_user: User = Depends(get_current_user)):
    """
    退出登录

    JWT 为无状态令牌，服务端不维护会话；前端清除本地 token 即可。
    """
    return success(message="退出成功")

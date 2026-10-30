"""
认证服务
"""
from typing import Optional

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import BusinessException
from core.security import hash_password, verify_password
from models.user import User
from schemas.auth import ProfileUpdateRequest
from services.storage_service import storage_service


class AuthService:
    """登录认证"""

    async def authenticate_user(
        self,
        username: str,
        password: str,
        db: AsyncSession,
    ) -> Optional[User]:
        """
        校验用户名密码

        Returns:
            校验通过返回 User；用户名不存在或密码错误返回 None
        """
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()

        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user

    async def update_profile(
        self,
        user: User,
        payload: ProfileUpdateRequest,
        db: AsyncSession,
    ) -> User:
        """修改昵称 / 邮箱"""
        data = payload.model_dump(exclude_unset=True)

        if "nickname" in data:
            user.nickname = data["nickname"] or None
        if "email" in data:
            user.email = data["email"] or None

        await db.commit()
        await db.refresh(user)
        return user

    async def change_password(
        self,
        user: User,
        old_password: str,
        new_password: str,
        db: AsyncSession,
    ) -> None:
        """修改本人密码：先校验原密码"""
        if not verify_password(old_password, user.password_hash):
            raise BusinessException("原密码错误")

        user.password_hash = hash_password(new_password)
        await db.commit()

    async def update_avatar(
        self,
        user: User,
        file: UploadFile,
        db: AsyncSession,
    ) -> User:
        """上传头像并更新用户头像路径"""
        old_url = user.avatar_url
        new_url = await storage_service.save_avatar(file, user.user_id)

        user.avatar_url = new_url
        await db.commit()
        await db.refresh(user)

        # 清理旧头像文件
        storage_service.delete_avatar(old_url)

        return user


# 全局实例
auth_service = AuthService()

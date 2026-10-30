"""
认证服务
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import verify_password
from models.user import User


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


# 全局实例
auth_service = AuthService()

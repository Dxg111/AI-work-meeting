"""
安全模块：JWT + bcrypt + 登录鉴权依赖

阶段2：
- 登录时校验 bcrypt 密码并签发 JWT
- 业务接口通过 get_current_user 依赖校验 Bearer Token
- require_super_admin 供阶段3的后台管理接口使用
"""
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from core.database import get_db
from core.exceptions import ForbiddenException, UnauthorizedException
from models.user import User

# auto_error=False：缺失 token 时由我们返回统一格式的 401
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """对密码进行 bcrypt 哈希（cost=12）"""
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(rounds=12),
    ).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验密码；无效哈希按校验失败处理"""
    if not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT token，payload 中携带 user_id、role、dept_id 等"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """解析 JWT token，失败返回 None"""
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    获取当前登录用户

    - 未携带 token / token 无效 → 401
    - 用户不存在 → 401
    - 账号被禁用 → 403
    """
    if credentials is None:
        raise UnauthorizedException("未登录或登录已过期")

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise UnauthorizedException("登录已过期，请重新登录")

    user_id = payload.get("user_id")
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise UnauthorizedException("登录凭证无效")

    user = await db.get(User, user_id)
    if not user:
        raise UnauthorizedException("用户不存在")

    if not user.is_active:
        raise ForbiddenException("账号已被禁用，请联系管理员")

    return user


async def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    """仅超级管理员可访问（阶段3后台管理接口使用）"""
    if current_user.role != "super_admin":
        raise ForbiddenException("无权限访问")
    return current_user

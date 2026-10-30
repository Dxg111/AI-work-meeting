"""
数据统计 API 路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.response import success
from core.security import get_current_user
from models.user import User
from services.stats_service import stats_service

router = APIRouter(prefix="/stats", tags=["数据统计"])


@router.get("", summary="统计首页数据")
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取统计首页数据

    - 超级管理员：全局统计 + 分部门统计
    - 普通用户：个人统计（仅本人会议）
    """
    data = await stats_service.get_stats(current_user, db)
    return success(data=data)

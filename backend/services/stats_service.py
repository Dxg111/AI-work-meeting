"""
数据统计服务
"""
from datetime import date, datetime, time, timedelta
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.dept import Department
from models.meeting import Meeting
from models.user import User

STATUSES = [
    "uploaded",
    "transcribing",
    "transcribed",
    "summarizing",
    "done",
    "failed",
]


class StatsService:
    """会议数据统计"""

    async def get_stats(self, user: User, db: AsyncSession) -> dict:
        """
        获取统计首页数据

        - 超级管理员：全局统计 + 分部门统计
        - 普通用户：仅本人会议统计
        """
        is_super = user.role == "super_admin"

        conditions = []
        if not is_super:
            conditions.append(Meeting.create_user_id == user.user_id)

        # 1. 状态分布
        status_query = select(Meeting.status, func.count(Meeting.meeting_id))
        if conditions:
            status_query = status_query.where(and_(*conditions))
        status_query = status_query.group_by(Meeting.status)

        rows = await db.execute(status_query)
        counts = {status: 0 for status in STATUSES}
        for status, count in rows.all():
            counts[status] = count

        total = sum(counts.values())
        done = counts["done"]
        failed = counts["failed"]
        # 处理中：除已完成、失败外的所有状态（已上传/转写中/已转写/生成中）
        processing = total - done - failed

        # 2. 累计音频时长（秒）
        duration_query = select(func.coalesce(func.sum(Meeting.duration), 0))
        if conditions:
            duration_query = duration_query.where(and_(*conditions))
        total_duration = await db.scalar(duration_query) or 0

        # 3. 近 7 天新增会议
        today = date.today()
        start_date = today - timedelta(days=6)
        start_dt = datetime.combine(start_date, time.min)

        day_expr = func.date(Meeting.created_at)
        day_query = (
            select(day_expr, func.count(Meeting.meeting_id))
            .where(Meeting.created_at >= start_dt)
        )
        if conditions:
            day_query = day_query.where(and_(*conditions))
        day_query = day_query.group_by(day_expr)

        day_rows = await db.execute(day_query)
        day_map = {}
        for day, count in day_rows.all():
            key = day.isoformat() if hasattr(day, "isoformat") else str(day)
            day_map[key] = count

        last_7_days = []
        for i in range(7):
            current = start_date + timedelta(days=i)
            key = current.isoformat()
            last_7_days.append({"date": key, "count": day_map.get(key, 0)})

        # 4. 分部门统计（仅超级管理员）
        dept_distribution = []
        if is_super:
            dept_query = (
                select(Department.dept_name, func.count(Meeting.meeting_id))
                .outerjoin(User, User.dept_id == Department.dept_id)
                .outerjoin(Meeting, Meeting.create_user_id == User.user_id)
                .group_by(Department.dept_id, Department.dept_name)
                .order_by(Department.dept_id.asc())
            )
            dept_rows = await db.execute(dept_query)
            dept_distribution = [
                {"dept_name": name, "count": count}
                for name, count in dept_rows.all()
            ]

            # 未分配部门的用户会议
            unassigned = await db.scalar(
                select(func.count(Meeting.meeting_id))
                .select_from(Meeting)
                .join(User, Meeting.create_user_id == User.user_id)
                .where(User.dept_id.is_(None))
            )
            if unassigned:
                dept_distribution.append({"dept_name": "未分配", "count": unassigned})

        return {
            "role": user.role,
            "scope": "global" if is_super else "personal",
            "cards": {
                "total": total,
                "done": done,
                "processing": processing,
                "failed": failed,
                "total_duration": int(total_duration),
            },
            "status_distribution": [
                {"status": status, "count": counts[status]}
                for status in STATUSES
            ],
            "last_7_days": last_7_days,
            "dept_distribution": dept_distribution,
        }


# 全局实例
stats_service = StatsService()

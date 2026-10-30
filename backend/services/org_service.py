"""
组织管理服务（部门 / 用户）
"""
from typing import Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import BusinessException
from core.security import hash_password
from models.dept import Department
from models.meeting import Meeting
from models.user import User
from schemas.org import DeptCreate, DeptUpdate, UserCreate, UserUpdate


class OrgService:
    """部门与用户管理"""

    # ==================== 部门 ====================

    async def list_depts(
        self,
        page: int,
        page_size: int,
        keyword: Optional[str],
        db: AsyncSession,
    ):
        user_count = (
            select(func.count(User.user_id))
            .where(User.dept_id == Department.dept_id)
            .correlate(Department)
            .scalar_subquery()
        )

        conditions = []
        if keyword:
            conditions.append(Department.dept_name.like(f"%{keyword}%"))

        count_query = select(func.count(Department.dept_id))
        query = select(Department, user_count.label("user_count"))
        if conditions:
            count_query = count_query.where(and_(*conditions))
            query = query.where(and_(*conditions))

        total = await db.scalar(count_query)
        rows = await db.execute(
            query
            .order_by(Department.dept_id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        return rows.all(), total or 0

    async def list_dept_options(self, db: AsyncSession):
        result = await db.execute(
            select(Department.dept_id, Department.dept_name).order_by(Department.dept_name.asc())
        )
        return result.all()

    async def get_dept(self, dept_id: int, db: AsyncSession) -> Department:
        dept = await db.get(Department, dept_id)
        if not dept:
            raise BusinessException("部门不存在", code=404)
        return dept

    async def create_dept(self, payload: DeptCreate, db: AsyncSession) -> Department:
        name = payload.dept_name.strip()
        if not name:
            raise BusinessException("部门名称不能为空")

        exists = await db.scalar(
            select(func.count(Department.dept_id)).where(Department.dept_name == name)
        )
        if exists:
            raise BusinessException("部门名称已存在")

        dept = Department(dept_name=name, dept_desc=payload.dept_desc)
        db.add(dept)
        await db.commit()
        await db.refresh(dept)
        return dept

    async def update_dept(self, dept_id: int, payload: DeptUpdate, db: AsyncSession) -> Department:
        dept = await self.get_dept(dept_id, db)
        name = payload.dept_name.strip()
        if not name:
            raise BusinessException("部门名称不能为空")

        exists = await db.scalar(
            select(func.count(Department.dept_id)).where(
                Department.dept_name == name,
                Department.dept_id != dept_id,
            )
        )
        if exists:
            raise BusinessException("部门名称已存在")

        dept.dept_name = name
        dept.dept_desc = payload.dept_desc
        await db.commit()
        await db.refresh(dept)
        return dept

    async def delete_dept(self, dept_id: int, db: AsyncSession) -> None:
        dept = await self.get_dept(dept_id, db)

        user_count = await db.scalar(
            select(func.count(User.user_id)).where(User.dept_id == dept_id)
        )
        if user_count:
            raise BusinessException("部门下存在用户，无法删除，请先迁移或删除该部门用户")

        await db.delete(dept)
        await db.commit()

    # ==================== 用户 ====================

    async def list_user_options(self, db: AsyncSession):
        """用户下拉选项（用于会议列表按创建人筛选）"""
        result = await db.execute(
            select(User.user_id, User.username, User.nickname).order_by(User.username.asc())
        )
        return result.all()

    async def list_users(
        self,
        page: int,
        page_size: int,
        dept_id: Optional[int],
        keyword: Optional[str],
        db: AsyncSession,
    ):
        conditions = []
        if dept_id is not None:
            conditions.append(User.dept_id == dept_id)
        if keyword:
            like = f"%{keyword}%"
            conditions.append(or_(User.username.like(like), User.nickname.like(like)))

        count_query = select(func.count(User.user_id))
        query = select(User, Department).outerjoin(
            Department, User.dept_id == Department.dept_id
        )
        if conditions:
            count_query = count_query.where(and_(*conditions))
            query = query.where(and_(*conditions))

        total = await db.scalar(count_query)
        rows = await db.execute(
            query
            .order_by(User.user_id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return rows.all(), total or 0

    async def get_user(self, user_id: int, db: AsyncSession) -> User:
        user = await db.get(User, user_id)
        if not user:
            raise BusinessException("用户不存在", code=404)
        return user

    async def create_user(self, payload: UserCreate, db: AsyncSession) -> User:
        username = payload.username.strip()
        if not username:
            raise BusinessException("用户名不能为空")

        exists = await db.scalar(
            select(func.count(User.user_id)).where(User.username == username)
        )
        if exists:
            raise BusinessException("用户名已存在")

        if payload.dept_id is not None:
            await self.get_dept(payload.dept_id, db)

        user = User(
            username=username,
            password_hash=hash_password(payload.password),
            nickname=payload.nickname,
            role=payload.role,
            dept_id=payload.dept_id,
            is_active=True,
            must_change_password=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def update_user(self, user_id: int, payload: UserUpdate, db: AsyncSession) -> User:
        user = await self.get_user(user_id, db)
        data = payload.model_dump(exclude_unset=True)

        if "dept_id" in data and data["dept_id"] is not None:
            await self.get_dept(data["dept_id"], db)

        new_role = data.get("role", user.role)
        new_active = data.get("is_active", user.is_active)

        # 超级管理员账号不允许被禁用（包括通过编辑接口修改）
        if new_role == "super_admin" and not new_active:
            raise BusinessException("超级管理员账号不允许被禁用")

        # 将超级管理员降级时，系统必须至少保留一个启用的超级管理员
        if user.role == "super_admin" and new_role != "super_admin":
            await self._ensure_other_active_super_admin(user.user_id, db)

        for field in ("nickname", "email", "dept_id", "role", "is_active"):
            if field in data:
                setattr(user, field, data[field])

        await db.commit()
        await db.refresh(user)
        return user

    async def update_user_status(self, user_id: int, is_active: bool, db: AsyncSession) -> User:
        user = await self.get_user(user_id, db)

        if not is_active and user.role == "super_admin":
            raise BusinessException("超级管理员账号不允许被禁用")

        user.is_active = is_active
        await db.commit()
        await db.refresh(user)
        return user

    async def reset_password(self, user_id: int, new_password: str, db: AsyncSession) -> None:
        user = await self.get_user(user_id, db)
        user.password_hash = hash_password(new_password)
        user.must_change_password = True
        await db.commit()

    async def delete_user(self, user_id: int, current_admin_id: int, db: AsyncSession) -> None:
        user = await self.get_user(user_id, db)

        if user.user_id == current_admin_id:
            raise BusinessException("不能删除当前登录账号")

        if user.role == "super_admin":
            await self._ensure_other_active_super_admin(user.user_id, db)

        meeting_count = await db.scalar(
            select(func.count(Meeting.meeting_id)).where(Meeting.create_user_id == user_id)
        )
        if meeting_count:
            raise BusinessException("该用户存在会议数据，建议禁用账号而不是删除")

        await db.delete(user)
        await db.commit()

    async def _ensure_other_active_super_admin(self, exclude_user_id: int, db: AsyncSession) -> None:
        """确认除指定用户外，仍存在启用的超级管理员"""
        count = await db.scalar(
            select(func.count(User.user_id)).where(
                User.role == "super_admin",
                User.is_active.is_(True),
                User.user_id != exclude_user_id,
            )
        )
        if not count:
            raise BusinessException("系统至少保留一个启用的超级管理员")


# 全局实例
org_service = OrgService()

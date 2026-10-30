"""
组织管理 API 路由（仅超级管理员）
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.response import success
from core.security import require_super_admin
from models.dept import Department
from models.user import User
from schemas.org import (
    DeptCreate,
    DeptOut,
    DeptUpdate,
    OrgUserOut,
    ResetPasswordRequest,
    UserCreate,
    UserStatusRequest,
    UserUpdate,
)
from services.org_service import org_service

router = APIRouter(prefix="/org", tags=["组织管理"])


def _dept_out(dept: Department, user_count: int = 0) -> DeptOut:
    return DeptOut(
        dept_id=dept.dept_id,
        dept_name=dept.dept_name,
        dept_desc=dept.dept_desc,
        user_count=user_count,
        created_at=dept.created_at,
    )


def _user_out(user: User, dept: Optional[Department]) -> OrgUserOut:
    return OrgUserOut(
        user_id=user.user_id,
        username=user.username,
        nickname=user.nickname,
        email=user.email,
        role=user.role,
        dept_id=user.dept_id,
        dept_name=dept.dept_name if dept else None,
        is_active=user.is_active,
        created_at=user.created_at,
    )


# ==================== 部门管理 ====================

@router.get("/depts", summary="部门列表")
async def list_depts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None, description="部门名称搜索"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_super_admin),
):
    rows, total = await org_service.list_depts(page, page_size, keyword, db)
    return success(data={
        "list": [_dept_out(dept, user_count) for dept, user_count in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.get("/depts/options", summary="部门下拉选项")
async def dept_options(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_super_admin),
):
    rows = await org_service.list_dept_options(db)
    return success(data=[
        {"dept_id": dept_id, "dept_name": dept_name}
        for dept_id, dept_name in rows
    ])


@router.post("/depts", summary="新增部门")
async def create_dept(
    payload: DeptCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_super_admin),
):
    dept = await org_service.create_dept(payload, db)
    return success(data=_dept_out(dept, 0), message="部门创建成功")


@router.put("/depts/{dept_id}", summary="编辑部门")
async def update_dept(
    dept_id: int,
    payload: DeptUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_super_admin),
):
    dept = await org_service.update_dept(dept_id, payload, db)
    return success(data=_dept_out(dept), message="部门更新成功")


@router.delete("/depts/{dept_id}", summary="删除部门")
async def delete_dept(
    dept_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_super_admin),
):
    await org_service.delete_dept(dept_id, db)
    return success(message="部门删除成功")


# ==================== 用户管理 ====================

@router.get("/users", summary="用户列表")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    dept_id: Optional[int] = Query(None, description="按部门筛选"),
    keyword: Optional[str] = Query(None, description="用户名/昵称搜索"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_super_admin),
):
    rows, total = await org_service.list_users(page, page_size, dept_id, keyword, db)
    return success(data={
        "list": [_user_out(user, dept) for user, dept in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.post("/users", summary="新增用户")
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_super_admin),
):
    user = await org_service.create_user(payload, db)
    dept = await db.get(Department, user.dept_id) if user.dept_id else None
    return success(data=_user_out(user, dept), message="用户创建成功")


@router.put("/users/{user_id}", summary="编辑用户")
async def update_user(
    user_id: int,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_super_admin),
):
    user = await org_service.update_user(user_id, payload, db)
    dept = await db.get(Department, user.dept_id) if user.dept_id else None
    return success(data=_user_out(user, dept), message="用户更新成功")


@router.put("/users/{user_id}/status", summary="启用/禁用用户")
async def update_user_status(
    user_id: int,
    payload: UserStatusRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_super_admin),
):
    user = await org_service.update_user_status(user_id, payload.is_active, db)
    dept = await db.get(Department, user.dept_id) if user.dept_id else None
    return success(
        data=_user_out(user, dept),
        message="账号已启用" if payload.is_active else "账号已禁用",
    )


@router.put("/users/{user_id}/password", summary="重置用户密码")
async def reset_password(
    user_id: int,
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_super_admin),
):
    await org_service.reset_password(user_id, payload.new_password, db)
    return success(message="密码重置成功")


@router.delete("/users/{user_id}", summary="删除用户")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_super_admin),
):
    await org_service.delete_user(user_id, admin.user_id, db)
    return success(message="用户删除成功")

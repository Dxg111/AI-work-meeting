"""
会议数据权限工具

规则：
- 超级管理员：可查看、编辑全部会议
- 普通用户：
  - 可查看/编辑自己创建的会议
  - 可只读查看同部门中开启 share_dept 的会议，可导出，不可编辑/删除/重新处理/重命名
"""
from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import BusinessException, ForbiddenException
from models.meeting import Meeting
from models.user import User


def is_super_admin(user: User) -> bool:
    return user.role == "super_admin"


def can_view_meeting(meeting: Meeting, creator: Optional[User], user: User) -> bool:
    """是否可查看会议（详情 / 导出）"""
    if is_super_admin(user):
        return True

    if meeting.create_user_id == user.user_id:
        return True

    # 同部门分享：仅普通用户、双方都有部门、且分享开关开启
    if user.dept_id is None or creator is None or creator.dept_id is None:
        return False

    return bool(meeting.share_dept) and creator.dept_id == user.dept_id


def can_edit_meeting(meeting: Meeting, user: User) -> bool:
    """是否可编辑会议（删除 / 处理 / 重命名 / 修改分享）"""
    return is_super_admin(user) or meeting.create_user_id == user.user_id


async def get_meeting_for_user(
    db: AsyncSession,
    meeting_id: int,
    user: User,
    require_edit: bool = False,
) -> Tuple[Meeting, Optional[User]]:
    """
    查询会议并校验权限

    Args:
        require_edit: True 表示写操作，需要创建人或超级管理员权限

    Returns:
        (meeting, creator)

    Raises:
        BusinessException 404 / ForbiddenException 403
    """
    meeting = await db.get(Meeting, meeting_id)
    if not meeting:
        raise BusinessException("会议不存在", code=404)

    creator = await db.get(User, meeting.create_user_id)

    if require_edit:
        if not can_edit_meeting(meeting, user):
            raise ForbiddenException("无权限操作该会议")
    else:
        if not can_view_meeting(meeting, creator, user):
            raise ForbiddenException("无权限查看该会议")

    return meeting, creator

"""
用户模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean, ForeignKey
from sqlalchemy.sql import func
from models import Base


class User(Base):
    """用户表"""
    __tablename__ = "t_user"

    user_id = Column(Integer, primary_key=True, autoincrement=True, comment="用户ID")
    username = Column(String(50), nullable=False, unique=True, index=True, comment="用户名")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    nickname = Column(String(100), comment="昵称")
    email = Column(String(100), comment="邮箱")
    avatar_url = Column(String(500), comment="头像URL")
    role = Column(Enum('super_admin', 'normal_user'), nullable=False, default='normal_user', index=True, comment="角色")
    dept_id = Column(Integer, ForeignKey('t_dept.dept_id', ondelete='SET NULL'), index=True, comment="所属部门ID")
    is_active = Column(Boolean, nullable=False, default=True, comment="账号状态")
    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")

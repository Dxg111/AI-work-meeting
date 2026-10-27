"""
部门模型
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from models import Base


class Department(Base):
    """部门表"""
    __tablename__ = "t_dept"

    dept_id = Column(Integer, primary_key=True, autoincrement=True, comment="部门ID")
    dept_name = Column(String(100), nullable=False, unique=True, index=True, comment="部门名称")
    dept_desc = Column(String(500), comment="部门描述")
    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")

"""
SQLAlchemy 模型
导入所有模型以便 SQLAlchemy 能够正确识别表关系
"""
from core.database import Base

# 导入所有模型（顺序很重要：先导入被依赖的表）
from models.dept import Department
from models.user import User
from models.meeting import Meeting
from models.transcript import Transcript
from models.speaker import Speaker
from models.minutes import Minutes

__all__ = [
    "Base",
    "Department",
    "User",
    "Meeting",
    "Transcript",
    "Speaker",
    "Minutes"
]

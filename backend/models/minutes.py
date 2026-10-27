"""
会议纪要模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from models import Base


class Minutes(Base):
    """会议纪要表"""
    __tablename__ = "t_minutes"

    minutes_id = Column(Integer, primary_key=True, autoincrement=True, comment="纪要ID")
    meeting_id = Column(Integer, ForeignKey('t_meeting.meeting_id', ondelete='CASCADE'), nullable=False, unique=True, index=True, comment="所属会议ID")
    summary = Column(Text, comment="会议摘要")
    keywords = Column(String(500), comment="关键词（逗号分隔）")
    todos = Column(JSON, comment="待办事项JSON数组")
    speaker_summary = Column(JSON, comment="发言人总结JSON")
    markdown = Column(Text, comment="完整Markdown格式纪要")
    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")

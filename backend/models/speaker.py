"""
发言人模型
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from models import Base


class Speaker(Base):
    """发言人表"""
    __tablename__ = "t_speaker"

    speaker_pk = Column(Integer, primary_key=True, autoincrement=True, comment="发言人主键")
    meeting_id = Column(Integer, ForeignKey('t_meeting.meeting_id', ondelete='CASCADE'), nullable=False, index=True, comment="所属会议ID")
    speaker_id = Column(String(50), nullable=False, comment="原始说话人ID")
    speaker_name = Column(String(100), nullable=False, comment="发言人显示名称")
    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    __table_args__ = (
        UniqueConstraint('meeting_id', 'speaker_id', name='uk_meeting_speaker'),
    )

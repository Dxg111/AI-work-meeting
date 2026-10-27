"""
转写句子模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from models import Base


class Transcript(Base):
    """转写句子表"""
    __tablename__ = "t_transcript"

    transcript_id = Column(Integer, primary_key=True, autoincrement=True, comment="转写句子ID")
    meeting_id = Column(Integer, ForeignKey('t_meeting.meeting_id', ondelete='CASCADE'), nullable=False, index=True, comment="所属会议ID")
    speaker_id = Column(String(50), nullable=False, index=True, comment="说话人ID")
    sentence_index = Column(Integer, nullable=False, index=True, comment="句子序号")
    start_time = Column(Integer, nullable=False, comment="开始时间（毫秒）")
    end_time = Column(Integer, nullable=False, comment="结束时间（毫秒）")
    content = Column(Text, nullable=False, comment="转写文本内容")
    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")

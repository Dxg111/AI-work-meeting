"""
会议模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, Boolean, ForeignKey
from sqlalchemy.sql import func
from models import Base


class Meeting(Base):
    """会议表"""
    __tablename__ = "t_meeting"

    meeting_id = Column(Integer, primary_key=True, autoincrement=True, comment="会议ID")
    title = Column(String(200), nullable=False, index=True, comment="会议标题")
    file_path = Column(String(500), nullable=False, comment="音视频文件本地路径")
    file_url = Column(String(500), nullable=False, comment="音视频文件公网访问URL")
    duration = Column(Integer, comment="音频时长（秒）")
    status = Column(
        Enum('uploaded', 'transcribing', 'transcribed', 'summarizing', 'done', 'failed'),
        nullable=False,
        default='uploaded',
        index=True,
        comment="会议状态"
    )
    error_msg = Column(Text, comment="错误信息")
    asr_task_id = Column(String(100), comment="ASR任务ID")
    create_user_id = Column(Integer, ForeignKey('t_user.user_id', ondelete='CASCADE'), nullable=False, index=True, comment="创建人ID")
    share_dept = Column(Boolean, nullable=False, default=False, comment="部门内分享")
    auto_process = Column(Boolean, nullable=False, default=True, comment="自动处理")
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")

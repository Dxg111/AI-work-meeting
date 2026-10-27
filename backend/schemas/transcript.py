"""
转写相关数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TranscriptBase(BaseModel):
    """转写句子基础模型"""
    speaker_id: str = Field(..., description="说话人ID")
    sentence_index: int = Field(..., description="句子序号")
    start_time: int = Field(..., description="开始时间（毫秒）")
    end_time: int = Field(..., description="结束时间（毫秒）")
    content: str = Field(..., description="转写文本内容")


class TranscriptCreate(TranscriptBase):
    """创建转写句子"""
    meeting_id: int = Field(..., description="所属会议ID")


class TranscriptOut(TranscriptBase):
    """转写句子输出模型"""
    transcript_id: int
    meeting_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class SpeakerBase(BaseModel):
    """发言人基础模型"""
    speaker_id: str = Field(..., description="原始说话人ID")
    speaker_name: str = Field(..., description="发言人显示名称")


class SpeakerCreate(SpeakerBase):
    """创建发言人"""
    meeting_id: int = Field(..., description="所属会议ID")


class SpeakerOut(SpeakerBase):
    """发言人输出模型"""
    speaker_pk: int
    meeting_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SpeakerUpdateRequest(BaseModel):
    """发言人重命名请求"""
    speaker_id: str = Field(..., description="原始说话人ID")
    speaker_name: str = Field(..., min_length=1, max_length=100, description="新的显示名称")

"""
会议相关 Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class MeetingUploadRequest(BaseModel):
    """会议上传请求"""
    title: str = Field(..., description="会议标题")
    auto_process: bool = Field(True, description="是否自动处理")
    share_dept: bool = Field(False, description="是否部门内分享")


class MeetingListQuery(BaseModel):
    """会议列表查询"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页数量")
    title: Optional[str] = Field(None, description="标题搜索")
    status: Optional[str] = Field(None, description="状态筛选")


class MeetingResponse(BaseModel):
    """会议响应"""
    meeting_id: int
    title: str
    file_url: str
    duration: Optional[int]
    status: str
    error_msg: Optional[str]
    create_user_id: int
    share_dept: bool
    auto_process: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TranscriptResponse(BaseModel):
    """转写句子响应"""
    transcript_id: int
    meeting_id: int
    speaker_id: str
    sentence_index: int
    start_time: int
    end_time: int
    content: str

    class Config:
        from_attributes = True


class SpeakerResponse(BaseModel):
    """发言人响应"""
    speaker_pk: int
    meeting_id: int
    speaker_id: str
    speaker_name: str

    class Config:
        from_attributes = True


class SpeakerRenameRequest(BaseModel):
    """发言人重命名请求"""
    speakers: List[dict] = Field(..., description="发言人列表 [{speaker_id, speaker_name}]")


class MeetingDetailResponse(BaseModel):
    """会议详情响应"""
    meeting: MeetingResponse
    transcripts: List[TranscriptResponse]
    speakers: List[SpeakerResponse]
    minutes: Optional[dict] = None


class MeetingOut(BaseModel):
    """会议输出模型"""
    meeting_id: int
    title: str
    file_url: str
    duration: Optional[int] = None
    status: str
    error_msg: Optional[str] = None
    create_user_id: int
    share_dept: int
    auto_process: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MeetingDetailOut(BaseModel):
    """会议详情输出"""
    meeting: "MeetingOut"
    transcripts: List[TranscriptResponse]
    speakers: List[SpeakerResponse]
    minutes: Optional[dict] = None


class MeetingListOut(BaseModel):
    """会议列表输出"""
    list: List["MeetingOut"]
    total: int
    page: int
    page_size: int

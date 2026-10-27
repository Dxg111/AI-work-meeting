"""
会议纪要相关数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class TodoItem(BaseModel):
    """待办事项"""
    content: str = Field(..., description="待办内容")
    owner: Optional[str] = Field(None, description="负责人")
    deadline: Optional[str] = Field(None, description="截止时间")


class MinutesBase(BaseModel):
    """会议纪要基础模型"""
    summary: Optional[str] = Field(None, description="会议摘要")
    keywords: Optional[str] = Field(None, description="关键词（逗号分隔）")
    todos: Optional[List[TodoItem]] = Field(default_factory=list, description="待办事项列表")
    speaker_summary: Optional[Dict[str, str]] = Field(default_factory=dict, description="发言人总结")
    markdown: Optional[str] = Field(None, description="完整Markdown格式纪要")


class MinutesCreate(MinutesBase):
    """创建会议纪要"""
    meeting_id: int = Field(..., description="所属会议ID")


class MinutesOut(MinutesBase):
    """会议纪要输出模型"""
    minutes_id: int
    meeting_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MinutesDetailOut(BaseModel):
    """会议纪要详情（用于前端展示）"""
    summary: Optional[str] = None
    keywords: Optional[List[str]] = None  # 拆分为数组
    todos: List[TodoItem] = []
    speaker_summary: Dict[str, str] = {}
    markdown: Optional[str] = None

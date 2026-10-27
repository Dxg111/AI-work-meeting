"""
会议管理服务（状态机 + 流水线编排）
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, or_, and_
from fastapi import BackgroundTasks

from models.meeting import Meeting
from models.transcript import Transcript
from models.speaker import Speaker
from models.minutes import Minutes
from services.storage_service import storage_service
from services.asr_service import asr_service
from services.llm_service import llm_service
from core.exceptions import BusinessException


class MeetingService:
    """会议管理服务（状态机核心）"""

    async def create_meeting(
        self,
        title: str,
        file_path: str,
        file_url: str,
        auto_process: bool,
        share_dept: bool,
        create_user_id: int,
        db: AsyncSession
    ) -> Meeting:
        """
        创建会议记录

        Args:
            title: 会议标题
            file_path: 本地文件路径
            file_url: 公网访问URL
            auto_process: 是否自动处理
            share_dept: 是否部门分享
            create_user_id: 创建人ID（MVP阶段固定为1）
            db: 数据库会话

        Returns:
            Meeting: 创建的会议对象
        """
        meeting = Meeting(
            title=title,
            file_path=file_path,
            file_url=file_url,
            status="uploaded",
            create_user_id=create_user_id,
            share_dept=1 if share_dept else 0,
            auto_process=1 if auto_process else 0
        )

        db.add(meeting)
        await db.commit()
        await db.refresh(meeting)

        print(f"[Meeting] 创建会议成功: {meeting.meeting_id} - {title}")
        return meeting

    async def trigger_pipeline(
        self,
        meeting_id: int,
        db: AsyncSession,
        background_tasks: BackgroundTasks
    ) -> None:
        """
        触发完整处理流水线（ASR → LLM）

        Args:
            meeting_id: 会议ID
            db: 数据库会话
            background_tasks: FastAPI 后台任务
        """
        # 检查会议状态
        result = await db.execute(
            select(Meeting).where(Meeting.meeting_id == meeting_id)
        )
        meeting = result.scalar_one_or_none()

        if not meeting:
            raise BusinessException("会议不存在")

        # 检查状态（只有 uploaded 或 failed 可以触发）
        if meeting.status not in ["uploaded", "failed", "transcribed"]:
            raise BusinessException(f"会议状态为 {meeting.status}，无法触发处理")

        # 检查公网URL
        is_valid, msg = storage_service.check_public_url_accessibility()
        if not is_valid:
            meeting.status = "failed"
            meeting.error_msg = msg
            await db.commit()
            raise BusinessException(msg)

        # 提交 ASR 任务
        try:
            await asr_service.submit_transcribe_task(meeting_id, meeting.file_url, db)
            print(f"[Pipeline] 会议 {meeting_id} 流水线已启动")
        except Exception as e:
            raise BusinessException(f"启动流水线失败: {str(e)}")

    async def get_meeting_detail(self, meeting_id: int, db: AsyncSession) -> Optional[dict]:
        """
        获取会议详情（包含转写、发言人、纪要）

        Args:
            meeting_id: 会议ID
            db: 数据库会话

        Returns:
            会议详情字典
        """
        # 查询会议基础信息
        meeting_result = await db.execute(
            select(Meeting).where(Meeting.meeting_id == meeting_id)
        )
        meeting = meeting_result.scalar_one_or_none()

        if not meeting:
            return None

        # 查询转写句子
        transcript_result = await db.execute(
            select(Transcript)
            .where(Transcript.meeting_id == meeting_id)
            .order_by(Transcript.sentence_index)
        )
        transcripts = transcript_result.scalars().all()

        # 查询发言人
        speaker_result = await db.execute(
            select(Speaker).where(Speaker.meeting_id == meeting_id)
        )
        speakers = speaker_result.scalars().all()

        # 查询纪要
        minutes_result = await db.execute(
            select(Minutes).where(Minutes.meeting_id == meeting_id)
        )
        minutes = minutes_result.scalar_one_or_none()

        return {
            "meeting": meeting,
            "transcripts": transcripts,
            "speakers": speakers,
            "minutes": minutes
        }

    async def delete_meeting(self, meeting_id: int, db: AsyncSession) -> None:
        """
        删除会议（级联删除关联数据）

        Args:
            meeting_id: 会议ID
            db: 数据库会话
        """
        # 查询会议
        result = await db.execute(
            select(Meeting).where(Meeting.meeting_id == meeting_id)
        )
        meeting = result.scalar_one_or_none()

        if not meeting:
            raise BusinessException("会议不存在")

        # 删除本地文件
        storage_service.delete_file(meeting.file_path)

        # 删除数据库记录（级联删除由外键约束处理）
        await db.delete(meeting)
        await db.commit()

        print(f"[Meeting] 删除会议成功: {meeting_id}")

    async def update_share_setting(
        self,
        meeting_id: int,
        share_dept: bool,
        db: AsyncSession
    ) -> None:
        """
        修改会议分享设置

        Args:
            meeting_id: 会议ID
            share_dept: 是否部门分享
            db: 数据库会话
        """
        result = await db.execute(
            select(Meeting).where(Meeting.meeting_id == meeting_id)
        )
        meeting = result.scalar_one_or_none()

        if not meeting:
            raise BusinessException("会议不存在")

        meeting.share_dept = 1 if share_dept else 0
        await db.commit()

        print(f"[Meeting] 会议 {meeting_id} 分享设置已更新: {share_dept}")

    async def mark_failed(self, meeting_id: int, error_msg: str, db: AsyncSession) -> None:
        """
        标记会议为失败状态

        Args:
            meeting_id: 会议ID
            error_msg: 错误信息
            db: 数据库会话
        """
        result = await db.execute(
            select(Meeting).where(Meeting.meeting_id == meeting_id)
        )
        meeting = result.scalar_one_or_none()

        if meeting:
            meeting.status = "failed"
            meeting.error_msg = error_msg
            await db.commit()


# 全局实例
meeting_service = MeetingService()

"""
ASR 语音转写服务
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from models.meeting import Meeting
from models.transcript import Transcript
from models.speaker import Speaker
from providers.factory import get_asr_provider
from providers.base import ASRResult
from core.exceptions import BusinessException


class ASRService:
    """ASR 转写服务"""

    def __init__(self):
        self.provider = get_asr_provider()

    async def submit_transcribe_task(self, meeting_id: int, audio_url: str, db: AsyncSession) -> str:
        """
        提交 ASR 转写任务

        Args:
            meeting_id: 会议ID
            audio_url: 音频公网URL
            db: 数据库会话

        Returns:
            task_id: ASR任务ID

        Raises:
            BusinessException: 提交失败
        """
        try:
            # 调用 Provider 提交任务
            task_id = await self.provider.submit_task(audio_url)

            # 更新会议记录：保存 task_id，状态改为 transcribing
            result = await db.execute(
                select(Meeting).where(Meeting.meeting_id == meeting_id)
            )
            meeting = result.scalar_one_or_none()

            if not meeting:
                raise BusinessException("会议不存在")

            meeting.asr_task_id = task_id
            meeting.status = "transcribing"
            meeting.error_msg = None  # 清空之前的错误

            await db.commit()

            print(f"[ASR] 会议 {meeting_id} 提交转写任务成功，task_id={task_id}")
            return task_id

        except Exception as e:
            await db.rollback()
            error_msg = f"提交 ASR 任务失败: {str(e)}"
            print(f"[ASR] {error_msg}")
            raise BusinessException(error_msg)

    async def poll_transcribe_result(self, meeting_id: int, task_id: str, db: AsyncSession) -> Optional[ASRResult]:
        """
        轮询 ASR 转写结果

        Args:
            meeting_id: 会议ID
            task_id: ASR任务ID
            db: 数据库会话

        Returns:
            ASRResult 或 None（任务进行中返回None）
        """
        try:
            # 查询任务结果
            result = await self.provider.query_task(task_id)

            if result.status == "running":
                return None  # 任务还在执行中

            if result.status == "failed":
                # 标记会议失败
                await self._mark_meeting_failed(meeting_id, result.error or "转写失败", db)
                return result

            if result.status == "succeeded":
                # 解析并保存转写结果
                await self._save_transcribe_result(meeting_id, result, db)
                return result

            return None

        except Exception as e:
            error_msg = f"查询 ASR 结果失败: {str(e)}"
            print(f"[ASR] {error_msg}")
            await self._mark_meeting_failed(meeting_id, error_msg, db)
            return None

    async def _save_transcribe_result(self, meeting_id: int, result: ASRResult, db: AsyncSession) -> None:
        """
        保存转写结果到数据库

        Args:
            meeting_id: 会议ID
            result: ASR转写结果
            db: 数据库会话
        """
        try:
            # 1. 清空旧的转写数据和发言人数据（重新处理的情况）
            await db.execute(delete(Transcript).where(Transcript.meeting_id == meeting_id))
            await db.execute(delete(Speaker).where(Speaker.meeting_id == meeting_id))

            # 2. 提取所有说话人ID（去重）
            speaker_ids = set()
            for sentence in result.sentences:
                speaker_ids.add(sentence["speaker_id"])

            # 3. 插入发言人记录
            for speaker_id in speaker_ids:
                speaker = Speaker(
                    meeting_id=meeting_id,
                    speaker_id=speaker_id,
                    speaker_name=speaker_id  # 初始名称等于ID，后续可重命名
                )
                db.add(speaker)

            # 4. 插入转写句子记录
            for sentence in result.sentences:
                transcript = Transcript(
                    meeting_id=meeting_id,
                    speaker_id=sentence["speaker_id"],
                    sentence_index=sentence["sentence_index"],
                    start_time=sentence["start"],
                    end_time=sentence["end"],
                    content=sentence["content"]
                )
                db.add(transcript)

            # 5. 更新会议状态为 transcribed
            meeting_result = await db.execute(
                select(Meeting).where(Meeting.meeting_id == meeting_id)
            )
            meeting = meeting_result.scalar_one()
            meeting.status = "transcribed"
            meeting.error_msg = None

            # 根据最后一句的结束时间补充音频时长（秒），用于统计
            if result.sentences:
                max_end_ms = max(int(s.get("end") or 0) for s in result.sentences)
                meeting.duration = max(1, round(max_end_ms / 1000))

            await db.commit()

            print(f"[ASR] 会议 {meeting_id} 转写结果保存成功，共 {len(result.sentences)} 句话，{len(speaker_ids)} 位发言人")

        except Exception as e:
            await db.rollback()
            error_msg = f"保存转写结果失败: {str(e)}"
            print(f"[ASR] {error_msg}")
            await self._mark_meeting_failed(meeting_id, error_msg, db)
            raise

    async def _mark_meeting_failed(self, meeting_id: int, error_msg: str, db: AsyncSession) -> None:
        """标记会议为失败状态"""
        try:
            result = await db.execute(
                select(Meeting).where(Meeting.meeting_id == meeting_id)
            )
            meeting = result.scalar_one_or_none()

            if meeting:
                meeting.status = "failed"
                meeting.error_msg = error_msg
                await db.commit()

        except Exception as e:
            await db.rollback()
            print(f"[ASR] 标记会议失败状态时出错: {e}")


# 全局实例
asr_service = ASRService()

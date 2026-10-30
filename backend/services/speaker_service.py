"""
发言人管理服务
"""
import json
from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import BusinessException
from models.meeting import Meeting
from models.minutes import Minutes
from models.speaker import Speaker
from models.transcript import Transcript
from services.llm_service import llm_service


class SpeakerService:
    """发言人管理服务"""

    async def rename_speaker(
        self,
        meeting_id: int,
        speaker_id: str,
        new_name: str,
        db: AsyncSession,
    ) -> None:
        """重命名单个发言人，并同步刷新 Markdown 纪要"""
        result = await db.execute(
            select(Speaker).where(
                Speaker.meeting_id == meeting_id,
                Speaker.speaker_id == speaker_id,
            )
        )
        speaker = result.scalar_one_or_none()

        if not speaker:
            raise BusinessException(f"发言人 {speaker_id} 不存在")

        speaker.speaker_name = new_name
        await db.commit()

        await self._refresh_markdown(meeting_id, db)
        print(f"[Speaker] 会议 {meeting_id} 的发言人 {speaker_id} 已重命名为: {new_name}")

    async def batch_rename_speakers(
        self,
        meeting_id: int,
        rename_map: Dict[str, str],
        db: AsyncSession,
    ) -> None:
        """批量重命名发言人，提交后统一刷新 Markdown 纪要"""
        if not rename_map:
            return

        result = await db.execute(
            select(Speaker).where(Speaker.meeting_id == meeting_id)
        )
        speakers = {speaker.speaker_id: speaker for speaker in result.scalars().all()}

        for speaker_id, new_name in rename_map.items():
            speaker = speakers.get(speaker_id)
            if not speaker:
                raise BusinessException(f"发言人 {speaker_id} 不存在")
            speaker.speaker_name = new_name

        await db.commit()

        # 页面展示通过 speaker_id -> speaker_name 映射实时更新；
        # 导出的 Markdown 是生成时落库的文本，需要在重命名后重新拼装。
        await self._refresh_markdown(meeting_id, db)

        print(f"[Speaker] 会议 {meeting_id} 批量重命名 {len(rename_map)} 位发言人")

    async def _refresh_markdown(self, meeting_id: int, db: AsyncSession) -> None:
        """用当前发言人名称重新生成 t_minutes.markdown"""
        minutes = (
            await db.execute(
                select(Minutes).where(Minutes.meeting_id == meeting_id)
            )
        ).scalar_one_or_none()

        if not minutes:
            return

        meeting = await db.get(Meeting, meeting_id)
        if not meeting:
            return

        transcripts = (
            await db.execute(
                select(Transcript)
                .where(Transcript.meeting_id == meeting_id)
                .order_by(Transcript.sentence_index)
            )
        ).scalars().all()

        speakers = (
            await db.execute(
                select(Speaker).where(Speaker.meeting_id == meeting_id)
            )
        ).scalars().all()
        speaker_name_map = {
            speaker.speaker_id: speaker.speaker_name for speaker in speakers
        }

        todos = self._as_list(minutes.todos)
        speaker_summary = self._as_dict(minutes.speaker_summary)

        minutes.markdown = llm_service._build_markdown(
            meeting.title,
            minutes.summary,
            minutes.keywords,
            todos,
            speaker_summary,
            speaker_name_map,
            transcripts,
        )
        await db.commit()

    @staticmethod
    def _as_list(value) -> List[dict]:
        if not value:
            return []
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except (ValueError, TypeError):
                return []
        return value if isinstance(value, list) else []

    @staticmethod
    def _as_dict(value) -> Dict[str, str]:
        if not value:
            return {}
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except (ValueError, TypeError):
                return {}
        return value if isinstance(value, dict) else {}


# 全局实例
speaker_service = SpeakerService()

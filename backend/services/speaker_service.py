"""
发言人管理服务
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.speaker import Speaker
from core.exceptions import BusinessException


class SpeakerService:
    """发言人管理服务"""

    async def rename_speaker(
        self,
        meeting_id: int,
        speaker_id: str,
        new_name: str,
        db: AsyncSession
    ) -> None:
        """
        重命名发言人

        Args:
            meeting_id: 会议ID
            speaker_id: 原始说话人ID
            new_name: 新的显示名称
            db: 数据库会话

        Raises:
            BusinessException: 发言人不存在
        """
        result = await db.execute(
            select(Speaker).where(
                Speaker.meeting_id == meeting_id,
                Speaker.speaker_id == speaker_id
            )
        )
        speaker = result.scalar_one_or_none()

        if not speaker:
            raise BusinessException(f"发言人 {speaker_id} 不存在")

        speaker.speaker_name = new_name
        await db.commit()

        print(f"[Speaker] 会议 {meeting_id} 的发言人 {speaker_id} 已重命名为: {new_name}")

    async def batch_rename_speakers(
        self,
        meeting_id: int,
        rename_map: dict[str, str],
        db: AsyncSession
    ) -> None:
        """
        批量重命名发言人

        Args:
            meeting_id: 会议ID
            rename_map: {speaker_id: new_name} 映射
            db: 数据库会话
        """
        for speaker_id, new_name in rename_map.items():
            await self.rename_speaker(meeting_id, speaker_id, new_name, db)


# 全局实例
speaker_service = SpeakerService()

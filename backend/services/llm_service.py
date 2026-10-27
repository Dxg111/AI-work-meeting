"""
LLM 纪要生成服务
"""
import json
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.meeting import Meeting
from models.transcript import Transcript
from models.speaker import Speaker
from models.minutes import Minutes
from providers.factory import get_llm_provider
from core.exceptions import BusinessException


class LLMService:
    """LLM 纪要生成服务"""

    def __init__(self):
        self.provider = get_llm_provider()

    async def generate_minutes(self, meeting_id: int, db: AsyncSession) -> None:
        """
        生成会议纪要（LangChain 4步链式调用）

        Args:
            meeting_id: 会议ID
            db: 数据库会话

        Raises:
            BusinessException: 生成失败
        """
        try:
            # 1. 检查会议状态
            meeting_result = await db.execute(
                select(Meeting).where(Meeting.meeting_id == meeting_id)
            )
            meeting = meeting_result.scalar_one_or_none()

            if not meeting:
                raise BusinessException("会议不存在")

            if meeting.status != "transcribed":
                raise BusinessException(f"会议状态为 {meeting.status}，必须先完成转写")

            # 更新状态为 summarizing
            meeting.status = "summarizing"
            meeting.error_msg = None
            await db.commit()

            # 2. 读取转写文本
            transcript_result = await db.execute(
                select(Transcript)
                .where(Transcript.meeting_id == meeting_id)
                .order_by(Transcript.sentence_index)
            )
            transcripts = transcript_result.scalars().all()

            if not transcripts:
                raise BusinessException("转写文本为空")

            # 3. 拼接完整转写文本
            full_text = "\n".join([f"[{t.speaker_id}] {t.content}" for t in transcripts])

            # 4. 按说话人分组文本
            speakers_text = {}
            for t in transcripts:
                if t.speaker_id not in speakers_text:
                    speakers_text[t.speaker_id] = []
                speakers_text[t.speaker_id].append(t.content)

            # 合并每个说话人的文本
            speakers_text = {k: " ".join(v) for k, v in speakers_text.items()}

            # 5. 调用 LLM Provider 生成纪要
            print(f"[LLM] 开始生成会议 {meeting_id} 的纪要...")
            result = await self.provider.generate_minutes(full_text, speakers_text)

            # 6. 获取发言人映射（显示名称）
            speaker_result = await db.execute(
                select(Speaker).where(Speaker.meeting_id == meeting_id)
            )
            speakers = speaker_result.scalars().all()
            speaker_name_map = {s.speaker_id: s.speaker_name for s in speakers}

            # 7. 拼装完整 Markdown
            markdown = self._build_markdown(
                meeting.title,
                result.summary,
                result.keywords,
                result.todos,
                result.speaker_summary,
                speaker_name_map,
                transcripts
            )

            # 8. 保存纪要到数据库
            await self._save_minutes(meeting_id, result, markdown, db)

            # 9. 更新会议状态为 done
            meeting.status = "done"
            meeting.error_msg = None
            await db.commit()

            print(f"[LLM] 会议 {meeting_id} 纪要生成成功")

        except Exception as e:
            await db.rollback()
            error_msg = f"生成纪要失败: {str(e)}"
            print(f"[LLM] {error_msg}")
            await self._mark_meeting_failed(meeting_id, error_msg, db)
            raise BusinessException(error_msg)

    async def _save_minutes(
        self,
        meeting_id: int,
        result,
        markdown: str,
        db: AsyncSession
    ) -> None:
        """保存纪要到数据库"""

        # 检查是否已存在纪要（重新生成的情况）
        minutes_result = await db.execute(
            select(Minutes).where(Minutes.meeting_id == meeting_id)
        )
        minutes = minutes_result.scalar_one_or_none()

        # 序列化 JSON 字段
        todos_json = json.dumps(result.todos, ensure_ascii=False) if result.todos else None
        speaker_summary_json = json.dumps(result.speaker_summary, ensure_ascii=False) if result.speaker_summary else None

        if minutes:
            # 更新已有纪要
            minutes.summary = result.summary
            minutes.keywords = result.keywords
            minutes.todos = todos_json
            minutes.speaker_summary = speaker_summary_json
            minutes.markdown = markdown
        else:
            # 新建纪要
            minutes = Minutes(
                meeting_id=meeting_id,
                summary=result.summary,
                keywords=result.keywords,
                todos=todos_json,
                speaker_summary=speaker_summary_json,
                markdown=markdown
            )
            db.add(minutes)

        await db.commit()

    def _build_markdown(
        self,
        title: str,
        summary: Optional[str],
        keywords: Optional[str],
        todos: List[Dict],
        speaker_summary: Dict[str, str],
        speaker_name_map: Dict[str, str],
        transcripts: List[Transcript]
    ) -> str:
        """
        拼装完整 Markdown 纪要

        Args:
            title: 会议标题
            summary: 摘要
            keywords: 关键词
            todos: 待办事项列表
            speaker_summary: 发言人总结
            speaker_name_map: 发言人ID到显示名称的映射
            transcripts: 转写句子列表

        Returns:
            完整的 Markdown 文本
        """
        lines = []

        # 标题
        lines.append(f"# {title}\n")

        # 会议摘要
        lines.append("## 📝 会议摘要\n")
        lines.append(summary or "（无摘要）")
        lines.append("\n")

        # 关键词
        lines.append("## 🔑 关键词\n")
        lines.append(keywords or "（无关键词）")
        lines.append("\n")

        # 待办事项
        lines.append("## ✅ 待办事项\n")
        if todos:
            lines.append("| 事项 | 负责人 | 截止时间 |")
            lines.append("|------|--------|----------|")
            for todo in todos:
                content = todo.get("content", "")
                owner = todo.get("owner") or "-"
                deadline = todo.get("deadline") or "-"
                lines.append(f"| {content} | {owner} | {deadline} |")
        else:
            lines.append("（无待办事项）")
        lines.append("\n")

        # 发言人总结
        lines.append("## 👥 发言人总结\n")
        if speaker_summary:
            for speaker_id, summary_text in speaker_summary.items():
                display_name = speaker_name_map.get(speaker_id, speaker_id)
                lines.append(f"**{display_name}**: {summary_text}\n")
        else:
            lines.append("（无发言人总结）")
        lines.append("\n")

        # 完整转写文本
        lines.append("## 📄 完整转写文本\n")
        for t in transcripts:
            display_name = speaker_name_map.get(t.speaker_id, t.speaker_id)
            start_sec = t.start_time // 1000
            end_sec = t.end_time // 1000
            time_str = f"{start_sec // 60:02d}:{start_sec % 60:02d} - {end_sec // 60:02d}:{end_sec % 60:02d}"
            lines.append(f"**[{time_str}] {display_name}**: {t.content}\n")

        return "\n".join(lines)

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
            print(f"[LLM] 标记会议失败状态时出错: {e}")


# 全局实例
llm_service = LLMService()

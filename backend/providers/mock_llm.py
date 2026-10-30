import asyncio
from typing import Dict, List, Any
from providers.base import LLMProvider, MinutesResult

class MockLLMProvider(LLMProvider):
    """Mock LLM Provider for testing"""

    async def generate_minutes(self, transcript_text: str, speakers_text: Dict[str, str]) -> MinutesResult:
        """生成模拟的会议纪要"""
        await asyncio.sleep(0.5)

        # 模拟生成摘要
        summary = "本次会议主要讨论了项目开发进度。前端开发预计下周完成，后端API已经准备就绪，测试环境搭建完成可以开始联调。需要注意移动端适配问题，计划下周一再次确认进度。"

        # 模拟提取关键词
        keywords = "项目进度,前端开发,后端API,测试环境,移动端适配"

        # 模拟待办事项
        todos = [
            {
                "content": "完成前端开发",
                "owner": "前端负责人",
                "deadline": "下周"
            },
            {
                "content": "进行前后端联调",
                "owner": "测试团队",
                "deadline": "本周"
            },
            {
                "content": "移动端适配优化",
                "owner": "前端负责人",
                "deadline": "待定"
            },
            {
                "content": "下周一进度会议",
                "owner": "全体成员",
                "deadline": "下周一"
            }
        ]

        # 模拟发言人总结
        speaker_summary = {}
        for speaker_id in speakers_text.keys():
            if speaker_id == "spk0":
                speaker_summary[speaker_id] = "主持会议，询问项目进展情况，确认后端API已就绪，安排下次会议时间"
            elif speaker_id == "spk1":
                speaker_summary[speaker_id] = "汇报前端开发进展，提出移动端适配需要注意的问题"
            elif speaker_id == "spk2":
                speaker_summary[speaker_id] = "确认测试环境搭建完成，可以开始前后端联调工作"
            else:
                speaker_summary[speaker_id] = "参与会议讨论，提供技术建议"

        return MinutesResult(
            summary=summary,
            keywords=keywords,
            todos=todos,
            speaker_summary=speaker_summary
        )

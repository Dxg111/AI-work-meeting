import asyncio
from typing import Dict, List, Any
from providers.base import LLMProvider

class MockLLMProvider(LLMProvider):
    async def generate_summary(self, transcript: str) -> str:
        await asyncio.sleep(0.5)
        return "本次会议讨论了项目开发进度"
    
    async def extract_keywords(self, transcript: str) -> str:
        await asyncio.sleep(0.3)
        return "项目进度,前端开发,后端API"
    
    async def extract_todos(self, transcript: str) -> List[Dict[str, Any]]:
        await asyncio.sleep(0.4)
        return [{"content": "前端优化", "owner": "张三", "deadline": "本周五"}]
    
    async def generate_speaker_summary(self, speaker_transcripts: Dict[str, str]) -> Dict[str, str]:
        await asyncio.sleep(0.4)
        return {sid: "参与会议讨论" for sid in speaker_transcripts.keys()}

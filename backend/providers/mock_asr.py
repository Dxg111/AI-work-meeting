import asyncio
from providers.base import ASRProvider, ASRResult

class MockASRProvider(ASRProvider):
    async def submit_task(self, audio_url: str, **kwargs) -> str:
        await asyncio.sleep(0.1)
        return f"mock_task_{hash(audio_url)}"
    
    async def query_task(self, task_id: str) -> ASRResult:
        await asyncio.sleep(0.2)
        mock_sentences = [
            {"speaker_id": "spk0", "start": 0, "end": 3000, "content": "测试会议内容"},
            {"speaker_id": "spk1", "start": 3500, "end": 7000, "content": "前端开发进展顺利"},
        ]
        return ASRResult(status="succeeded", sentences=mock_sentences, error=None)

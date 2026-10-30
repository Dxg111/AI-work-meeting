import asyncio
from providers.base import ASRProvider, ASRResult

class MockASRProvider(ASRProvider):
    async def submit_task(self, audio_url: str, **kwargs) -> str:
        await asyncio.sleep(0.1)
        return f"mock_task_{hash(audio_url)}"

    async def query_task(self, task_id: str) -> ASRResult:
        await asyncio.sleep(0.2)
        mock_sentences = [
            {
                "speaker_id": "spk0",
                "start": 0,
                "end": 3000,
                "content": "大家好，今天我们开会讨论项目进展。",
                "sentence_index": 0
            },
            {
                "speaker_id": "spk1",
                "start": 3500,
                "end": 7000,
                "content": "前端开发进展顺利，预计下周完成。",
                "sentence_index": 1
            },
            {
                "speaker_id": "spk0",
                "start": 7500,
                "end": 11000,
                "content": "很好，后端API已经准备就绪。",
                "sentence_index": 2
            },
            {
                "speaker_id": "spk2",
                "start": 11500,
                "end": 15000,
                "content": "测试环境已经搭建完成，可以开始联调。",
                "sentence_index": 3
            },
            {
                "speaker_id": "spk1",
                "start": 15500,
                "end": 19000,
                "content": "需要注意一下移动端适配的问题。",
                "sentence_index": 4
            },
            {
                "speaker_id": "spk0",
                "start": 19500,
                "end": 23000,
                "content": "好的，我们下周一再碰一次进度。",
                "sentence_index": 5
            },
        ]
        return ASRResult(status="succeeded", sentences=mock_sentences, error=None)

"""
阿里云百炼 Fun-ASR 真实实现（录音文件异步识别）

官方接口：
- 提交：POST /api/v1/services/audio/asr/transcription（需 X-DashScope-Async: enable）
- 查询：GET  /api/v1/tasks/{task_id}
- 成功后可下载 output.results[].transcription_url 对应的结果 JSON
"""
import httpx
from typing import Any

from .base import ASRProvider, ASRResult
from config import settings


class FunASRProvider(ASRProvider):
    """阿里云百炼 Fun-ASR 录音文件异步识别"""

    def __init__(self):
        self.api_key = settings.DASHSCOPE_API_KEY
        self.base_url = settings.ASR_BASE_URL.rstrip("/")
        self.model = settings.ASR_MODEL

    def _headers(self, async_submit: bool = False) -> dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if async_submit:
            # 录音文件识别是异步任务，必须携带该请求头
            headers["X-DashScope-Async"] = "enable"
        return headers

    async def submit_task(self, audio_url: str, **kwargs) -> str:
        """
        提交转写任务

        Args:
            audio_url: 音频文件公网 URL（必须能被阿里云侧下载）

        Returns:
            task_id: 异步任务 ID
        """
        if not self.api_key:
            raise Exception("未配置 DASHSCOPE_API_KEY，无法提交 Fun-ASR 任务")

        payload = {
            "model": self.model,
            "input": {
                "file_urls": [audio_url],
            },
            "parameters": {
                "diarization_enabled": True,  # 说话人分离
                "language_hints": ["zh"],
            },
        }

        # 允许调用方覆盖部分参数（如 speaker_count）
        speaker_count = kwargs.get("speaker_count")
        if speaker_count:
            payload["parameters"]["speaker_count"] = int(speaker_count)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/services/audio/asr/transcription",
                json=payload,
                headers=self._headers(async_submit=True),
            )

        if response.status_code != 200:
            raise Exception(f"Fun-ASR 提交失败: HTTP {response.status_code} {response.text[:300]}")

        result = response.json()

        # 成功响应没有顶层 code；失败响应通常带 code/message
        if result.get("code"):
            raise Exception(f"Fun-ASR 提交失败: {result.get('code')} {result.get('message')}")

        task_id = (result.get("output") or {}).get("task_id")
        if not task_id:
            raise Exception(f"Fun-ASR 返回的 task_id 为空: {str(result)[:300]}")

        return task_id

    async def query_task(self, task_id: str) -> ASRResult:
        """
        查询转写任务结果

        Args:
            task_id: 任务 ID

        Returns:
            ASRResult: running / succeeded / failed
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/tasks/{task_id}",
                headers=self._headers(),
            )

        if response.status_code != 200:
            return ASRResult(
                status="failed",
                sentences=[],
                error=f"查询 Fun-ASR 任务失败: HTTP {response.status_code} {response.text[:200]}",
            )

        result = response.json()
        if result.get("code"):
            return ASRResult(
                status="failed",
                sentences=[],
                error=f"查询 Fun-ASR 任务失败: {result.get('code')} {result.get('message')}",
            )

        output = result.get("output") or {}
        task_status = str(output.get("task_status") or "").upper()

        if task_status in ("PENDING", "RUNNING"):
            return ASRResult(status="running", sentences=[])

        if task_status in ("FAILED", "CANCELED", "UNKNOWN"):
            error_msg = output.get("message") or result.get("message") or f"转写任务状态异常: {task_status}"
            return ASRResult(status="failed", sentences=[], error=error_msg)

        if task_status != "SUCCEEDED":
            return ASRResult(status="failed", sentences=[], error=f"未知任务状态: {task_status}")

        # 任务成功：逐个下载结果 JSON 并解析
        sentences: list[dict] = []
        results = output.get("results") or []

        for item in results:
            if str(item.get("subtask_status") or "").upper() == "FAILED":
                error_msg = item.get("message") or "子任务转写失败"
                return ASRResult(status="failed", sentences=[], error=error_msg)

            transcription_url = item.get("transcription_url")
            if not transcription_url:
                continue

            try:
                transcription = await self._download_result(transcription_url)
                sentences.extend(self._parse_transcript(transcription, len(sentences)))
            except Exception as e:
                return ASRResult(
                    status="failed",
                    sentences=[],
                    error=f"下载/解析转写结果失败: {str(e)}",
                )

        if not sentences:
            return ASRResult(status="failed", sentences=[], error="转写结果为空")

        return ASRResult(status="succeeded", sentences=sentences)

    async def _download_result(self, url: str) -> dict:
        """下载 transcription_url 指向的结果 JSON"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url)
        if response.status_code != 200:
            raise Exception(f"下载结果失败: HTTP {response.status_code}")
        return response.json()

    def _parse_transcript(self, data: dict, start_index: int) -> list[dict]:
        """
        解析 Fun-ASR 结果 JSON

        结构示例：
        {
          "transcripts": [
            {"channel_id": 0, "text": "...", "sentences": [
                {"begin_time": 0, "end_time": 1000, "text": "...", "speaker_id": 0}
            ]}
          ]
        }
        """
        sentences: list[dict] = []
        index = start_index

        transcripts = data.get("transcripts") or []

        # 兼容部分返回直接给 sentences 的情况
        if not transcripts and data.get("sentences"):
            transcripts = [{"sentences": data["sentences"]}]

        for transcript in transcripts:
            for item in transcript.get("sentences") or []:
                content = (item.get("text") or "").strip()
                if not content:
                    continue

                speaker = item.get("speaker_id")
                if speaker is None:
                    speaker = item.get("speaker", "spk0")
                if isinstance(speaker, int):
                    speaker = f"spk{speaker}"

                sentences.append({
                    "speaker_id": str(speaker),
                    "start": int(item.get("begin_time") or 0),
                    "end": int(item.get("end_time") or 0),
                    "content": content,
                    "sentence_index": index,
                })
                index += 1

            # 没有句子级结果时，退化为整段文本
            if not transcript.get("sentences"):
                content = (transcript.get("text") or "").strip()
                if content:
                    sentences.append({
                        "speaker_id": "spk0",
                        "start": 0,
                        "end": 0,
                        "content": content,
                        "sentence_index": index,
                    })
                    index += 1

        return sentences

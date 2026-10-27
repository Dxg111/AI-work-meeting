"""
阿里云百炼 Fun-ASR 真实实现
"""
import httpx
from typing import Optional
from .base import ASRProvider, ASRResult
from config import settings


class FunASRProvider(ASRProvider):
    """阿里云百炼 Fun-ASR 录音文件异步识别"""

    def __init__(self):
        self.api_key = settings.DASHSCOPE_API_KEY
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/audio/asr"

    async def submit_task(self, audio_url: str) -> str:
        """
        提交转写任务

        Args:
            audio_url: 音频文件公网URL

        Returns:
            task_id: 任务ID

        Raises:
            Exception: 提交失败时抛出异常
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "paraformer-realtime-v2",
            "input": {
                "url": audio_url
            },
            "parameters": {
                "format": "mp3",  # 根据实际文件格式调整
                "sample_rate": 16000,
                "enable_diarization": True,  # 开启说话人分离
                "diarization_num": -1  # 自动检测说话人数量
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/submit",
                json=payload,
                headers=headers
            )

            if response.status_code != 200:
                raise Exception(f"Fun-ASR 提交失败: {response.status_code} {response.text}")

            result = response.json()

            if result.get("code") != "200":
                raise Exception(f"Fun-ASR 提交失败: {result.get('message')}")

            task_id = result.get("output", {}).get("task_id")

            if not task_id:
                raise Exception("Fun-ASR 返回的 task_id 为空")

            return task_id

    async def query_task(self, task_id: str) -> ASRResult:
        """
        查询转写任务结果

        Args:
            task_id: 任务ID

        Returns:
            ASRResult: 转写结果
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/query",
                params={"task_id": task_id},
                headers=headers
            )

            if response.status_code != 200:
                return ASRResult(
                    status="failed",
                    sentences=[],
                    error=f"查询失败: HTTP {response.status_code}"
                )

            result = response.json()

            # 解析任务状态
            task_status = result.get("output", {}).get("task_status", "").lower()

            if task_status == "running" or task_status == "pending":
                return ASRResult(status="running", sentences=[])

            if task_status == "failed":
                error_msg = result.get("output", {}).get("error_message", "转写失败")
                return ASRResult(status="failed", sentences=[], error=error_msg)

            if task_status == "succeeded":
                # 解析转写结果
                sentences = self._parse_transcript(result)
                return ASRResult(status="succeeded", sentences=sentences)

            return ASRResult(
                status="failed",
                sentences=[],
                error=f"未知状态: {task_status}"
            )

    def _parse_transcript(self, result: dict) -> list[dict]:
        """
        解析 Fun-ASR 返回的转写结果

        Args:
            result: API 返回的完整结果

        Returns:
            句子列表: [{speaker_id, start, end, content}]
        """
        sentences = []

        # Fun-ASR 返回格式示例（实际格式可能不同，需根据真实返回调整）
        transcripts = result.get("output", {}).get("results", [])

        for idx, item in enumerate(transcripts):
            sentence = {
                "speaker_id": item.get("speaker", "spk0"),  # 说话人ID
                "start": int(item.get("begin_time", 0)),  # 开始时间（毫秒）
                "end": int(item.get("end_time", 0)),  # 结束时间（毫秒）
                "content": item.get("text", "").strip(),  # 转写文本
                "sentence_index": idx
            }

            if sentence["content"]:  # 过滤空句子
                sentences.append(sentence)

        return sentences

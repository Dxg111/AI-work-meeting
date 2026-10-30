from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class ASRResult:
    """ASR 转写结果"""
    status: str
    sentences: List[Dict[str, Any]]
    error: Optional[str] = None

@dataclass
class MinutesResult:
    """LLM 纪要生成结果"""
    summary: Optional[str] = None
    keywords: Optional[str] = None
    todos: List[Dict[str, Any]] = field(default_factory=list)
    speaker_summary: Dict[str, str] = field(default_factory=dict)

class ASRProvider(ABC):
    """ASR 服务提供者抽象基类"""
    
    @abstractmethod
    async def submit_task(self, audio_url: str, **kwargs) -> str:
        """提交 ASR 任务"""
        pass
    
    @abstractmethod
    async def query_task(self, task_id: str) -> ASRResult:
        """查询 ASR 任务结果"""
        pass

class LLMProvider(ABC):
    """LLM 服务提供者抽象基类"""
    
    @abstractmethod
    async def generate_minutes(self, transcript_text: str, speakers_text: Dict[str, str]) -> MinutesResult:
        """生成会议纪要"""
        pass

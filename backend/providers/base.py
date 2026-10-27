from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class ASRResult:
    status: str
    sentences: List[Dict[str, Any]]
    error: Optional[str] = None

class ASRProvider(ABC):
    @abstractmethod
    async def submit_task(self, audio_url: str, **kwargs) -> str:
        pass
    @abstractmethod
    async def query_task(self, task_id: str) -> ASRResult:
        pass

class LLMProvider(ABC):
    @abstractmethod
    async def generate_summary(self, transcript: str) -> str:
        pass
    @abstractmethod
    async def extract_keywords(self, transcript: str) -> str:
        pass
    @abstractmethod
    async def extract_todos(self, transcript: str) -> List[Dict[str, Any]]:
        pass
    @abstractmethod
    async def generate_speaker_summary(self, speaker_transcripts: Dict[str, str]) -> Dict[str, str]:
        pass

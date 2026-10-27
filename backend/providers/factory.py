"""
Provider 工厂函数
"""
from config import settings
from .base import ASRProvider, LLMProvider
from .mock_asr import MockASRProvider
from .mock_llm import MockLLMProvider
from .funasr import FunASRProvider
from .qwen_llm import QwenLLMProvider


def get_asr_provider() -> ASRProvider:
    """根据配置返回 ASR Provider 实例"""
    if settings.ASR_PROVIDER == "mock":
        return MockASRProvider()
    elif settings.ASR_PROVIDER == "funasr":
        return FunASRProvider()
    else:
        raise ValueError(f"未知的 ASR Provider: {settings.ASR_PROVIDER}")


def get_llm_provider() -> LLMProvider:
    """根据配置返回 LLM Provider 实例"""
    if settings.LLM_PROVIDER == "mock":
        return MockLLMProvider()
    elif settings.LLM_PROVIDER == "qwen":
        return QwenLLMProvider()
    else:
        raise ValueError(f"未知的 LLM Provider: {settings.LLM_PROVIDER}")

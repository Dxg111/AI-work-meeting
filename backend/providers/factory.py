from config import settings
from providers.base import ASRProvider, LLMProvider
from providers.mock_asr import MockASRProvider
from providers.mock_llm import MockLLMProvider

def get_asr_provider() -> ASRProvider:
    if settings.ASR_PROVIDER == "mock":
        return MockASRProvider()
    raise ValueError("ASR Provider not supported")

def get_llm_provider() -> LLMProvider:
    if settings.LLM_PROVIDER == "mock":
        return MockLLMProvider()
    raise ValueError("LLM Provider not supported")

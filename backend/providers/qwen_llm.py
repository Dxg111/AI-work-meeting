"""
通义千问 LangChain 真实实现
"""
import json
import re
from typing import Optional, List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from .base import LLMProvider, MinutesResult
from config import settings


class QwenLLMProvider(LLMProvider):
    """基于 LangChain + 通义千问的纪要生成"""

    def __init__(self):
        self.llm = ChatOpenAI(
            base_url=settings.LLM_BASE_URL,
            api_key=settings.DASHSCOPE_API_KEY,
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS
        )

    async def generate_minutes(
        self,
        transcript_text: str,
        speakers_text: Dict[str, str]
    ) -> MinutesResult:
        """
        生成会议纪要（4步链式调用）

        Args:
            transcript_text: 完整转写文本
            speakers_text: 按说话人分组的文本 {speaker_id: "该人说的所有话"}

        Returns:
            MinutesResult: 纪要生成结果
        """
        result = MinutesResult()

        # 步骤1: 生成全文摘要
        result.summary = await self._generate_summary(transcript_text)

        # 步骤2: 提取关键词
        result.keywords = await self._extract_keywords(transcript_text)

        # 步骤3: 提取待办事项
        result.todos = await self._extract_todos(transcript_text)

        # 步骤4: 生成发言人总结
        result.speaker_summary = await self._generate_speaker_summary(speakers_text)

        return result

    async def _generate_summary(self, text: str) -> Optional[str]:
        """生成会议摘要"""
        try:
            prompt = PromptTemplate.from_template(
                "你是一个专业的会议纪要助手。请根据以下会议转写内容，生成一份300字以内的中文会议摘要。\n\n"
                "要求：\n"
                "1. 简洁明了，突出核心内容\n"
                "2. 使用中文\n"
                "3. 不要超过300字\n"
                "4. 直接输出摘要内容，不要添加任何前缀或标题\n\n"
                "会议内容：\n{text}\n\n"
                "会议摘要："
            )

            chain = prompt | self.llm | StrOutputParser()
            summary = await chain.ainvoke({"text": text[:4000]})  # 限制输入长度

            return summary.strip()
        except Exception as e:
            print(f"[LLM] 生成摘要失败: {e}")
            return None

    async def _extract_keywords(self, text: str) -> Optional[str]:
        """提取关键词"""
        try:
            prompt = PromptTemplate.from_template(
                "你是一个专业的会议纪要助手。请从以下会议转写内容中提取5-10个关键词。\n\n"
                "要求：\n"
                "1. 关键词用中文逗号分隔\n"
                "2. 只输出关键词，不要其他内容\n"
                "3. 示例格式：项目进度,技术方案,资源分配,风险评估\n\n"
                "会议内容：\n{text}\n\n"
                "关键词："
            )

            chain = prompt | self.llm | StrOutputParser()
            keywords = await chain.ainvoke({"text": text[:4000]})

            return keywords.strip()
        except Exception as e:
            print(f"[LLM] 提取关键词失败: {e}")
            return None

    async def _extract_todos(self, text: str) -> List[Dict[str, Any]]:
        """提取待办事项"""
        try:
            prompt = PromptTemplate.from_template(
                "你是一个专业的会议纪要助手。请从以下会议内容中提取待办事项。\n\n"
                "要求：\n"
                "1. 输出严格的JSON数组格式\n"
                "2. 每个待办包含：content（事项内容）、owner（负责人，可为null）、deadline（截止时间，可为null）\n"
                "3. 如果没有明确的待办事项，返回空数组 []\n"
                "4. 不要添加markdown代码块标记，直接输出JSON\n\n"
                "示例输出：\n"
                '[{{"content": "完成需求文档", "owner": "张三", "deadline": "本周五"}}, '
                '{{"content": "联系供应商", "owner": null, "deadline": null}}]\n\n'
                "会议内容：\n{text}\n\n"
                "待办事项JSON："
            )

            chain = prompt | self.llm | StrOutputParser()
            result = await chain.ainvoke({"text": text[:4000]})

            # 清洗输出（去除可能的代码块标记）
            result = self._clean_json_output(result)

            # 解析JSON
            todos = json.loads(result)

            if not isinstance(todos, list):
                return []

            return todos

        except Exception as e:
            print(f"[LLM] 提取待办事项失败: {e}")
            return []

    async def _generate_speaker_summary(self, speakers_text: Dict[str, str]) -> Dict[str, str]:
        """生成发言人总结"""
        speaker_summary = {}

        for speaker_id, text in speakers_text.items():
            try:
                prompt = PromptTemplate.from_template(
                    "请用一句话总结以下发言人在会议中的主要观点和贡献（50字以内）：\n\n"
                    "{text}\n\n"
                    "总结："
                )

                chain = prompt | self.llm | StrOutputParser()
                summary = await chain.ainvoke({"text": text[:2000]})

                speaker_summary[speaker_id] = summary.strip()

            except Exception as e:
                print(f"[LLM] 生成发言人 {speaker_id} 总结失败: {e}")
                speaker_summary[speaker_id] = ""

        return speaker_summary

    @staticmethod
    def _clean_json_output(text: str) -> str:
        """清洗 LLM 输出的 JSON（去除 markdown 代码块）"""
        # 去除 ```json ... ``` 或 ``` ... ```
        text = re.sub(r'^```(?:json)?\s*', '', text.strip())
        text = re.sub(r'\s*```$', '', text.strip())
        return text.strip()

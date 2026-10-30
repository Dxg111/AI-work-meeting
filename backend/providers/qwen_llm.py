"""
通义千问 LangChain 真实实现

长文本（默认超过 8000 字符）自动启用 Map-Reduce：
- 摘要：分段摘要 -> 汇总摘要
- 关键词：分段提取 -> 去重合并
- 待办：分段提取 JSON -> 去重合并
- 发言人总结：分段总结 -> 汇总
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
        """生成会议纪要（4步链式调用，长文本自动 Map-Reduce）"""
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

    # ==================== 长文本分段 ====================

    def _chunk_text(self, text: str, chunk_size: Optional[int] = None) -> List[str]:
        """
        按行分段，尽量不切断完整句子。

        - 单行超长时按字符切分
        - 超过 LLM_MAP_MAX_CHUNKS 时只保留前 N 段
        """
        size = chunk_size or settings.LLM_MAP_CHUNK_CHARS
        chunks: List[str] = []
        current: List[str] = []
        current_len = 0

        for line in text.splitlines():
            # 超长单行按字符切分
            while len(line) > size:
                if current:
                    chunks.append("\n".join(current))
                    current = []
                    current_len = 0
                chunks.append(line[:size])
                line = line[size:]

            if current_len + len(line) + 1 > size and current:
                chunks.append("\n".join(current))
                current = []
                current_len = 0

            if line:
                current.append(line)
                current_len += len(line) + 1

        if current:
            chunks.append("\n".join(current))

        if len(chunks) > settings.LLM_MAP_MAX_CHUNKS:
            print(
                f"[LLM] 文本过长，分段数 {len(chunks)} 超过上限 "
                f"{settings.LLM_MAP_MAX_CHUNKS}，仅处理前 {settings.LLM_MAP_MAX_CHUNKS} 段"
            )
            chunks = chunks[:settings.LLM_MAP_MAX_CHUNKS]

        return [chunk for chunk in chunks if chunk.strip()]

    # ==================== 摘要 ====================

    async def _generate_summary(self, text: str) -> Optional[str]:
        """生成会议摘要（长文本 Map-Reduce）"""
        try:
            if len(text) <= settings.LLM_MAP_THRESHOLD_CHARS:
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
                summary = await chain.ainvoke({"text": text})
                return summary.strip()

            chunks = self._chunk_text(text)
            if not chunks:
                return None

            print(f"[LLM] 长文本摘要 Map-Reduce：{len(chunks)} 段")
            partial_prompt = PromptTemplate.from_template(
                "你是会议纪要助手。这是会议转写的第 {index}/{total} 部分。\n"
                "请用200字以内中文概括这部分的核心内容、结论和待定事项。\n"
                "只输出摘要正文，不要加标题或编号。\n\n"
                "内容：\n{text}\n\n部分摘要："
            )
            partial_chain = partial_prompt | self.llm | StrOutputParser()

            partials: List[str] = []
            for index, chunk in enumerate(chunks, start=1):
                try:
                    partial = await partial_chain.ainvoke({
                        "text": chunk,
                        "index": index,
                        "total": len(chunks),
                    })
                    if partial.strip():
                        partials.append(partial.strip())
                except Exception as e:
                    print(f"[LLM] 第 {index} 段摘要失败: {e}")

            if not partials:
                return None

            combined = "\n".join(
                f"第{i}部分：{partial}" for i, partial in enumerate(partials, start=1)
            )
            final_prompt = PromptTemplate.from_template(
                "以下是同一场会议各部分的摘要。请综合成一份300字以内的中文会议摘要。\n"
                "要求：突出结论、决策、关键进展和风险；不要出现“第1部分”等编号；只输出摘要正文。\n\n"
                "{text}\n\n最终摘要："
            )
            final_chain = final_prompt | self.llm | StrOutputParser()
            summary = await final_chain.ainvoke({"text": combined})
            return summary.strip()

        except Exception as e:
            print(f"[LLM] 生成摘要失败: {e}")
            return None

    # ==================== 关键词 ====================

    async def _extract_keywords(self, text: str) -> Optional[str]:
        """提取关键词（长文本分段提取后合并）"""
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
            # 提取类任务固定 temperature=0，保证结果稳定
            chain = prompt | self.llm.bind(temperature=0) | StrOutputParser()

            if len(text) <= settings.LLM_MAP_THRESHOLD_CHARS:
                keywords = await chain.ainvoke({"text": text})
                return keywords.strip()

            chunks = self._chunk_text(text)
            if not chunks:
                return None

            print(f"[LLM] 长文本关键词分段提取：{len(chunks)} 段")
            collected: List[str] = []
            for index, chunk in enumerate(chunks, start=1):
                try:
                    result = await chain.ainvoke({"text": chunk})
                    collected.extend(re.split(r"[,，、\n]", result))
                except Exception as e:
                    print(f"[LLM] 第 {index} 段关键词提取失败: {e}")

            seen: List[str] = []
            for item in collected:
                keyword = item.strip()
                if keyword and keyword not in seen:
                    seen.append(keyword)

            return ",".join(seen[:15]) if seen else None

        except Exception as e:
            print(f"[LLM] 提取关键词失败: {e}")
            return None

    # ==================== 待办 ====================

    async def _extract_todos(self, text: str) -> List[Dict[str, Any]]:
        """提取待办事项（长文本分段提取后去重合并）"""
        try:
            prompt = PromptTemplate.from_template(
                "你是会议纪要助手。请从会议内容中提取所有行动项/待办事项，"
                "包括“预计完成”“下周再碰”“需要注意”这类隐含行动。\n\n"
                "要求：\n"
                "1. 只输出严格的JSON数组，不要任何解释或markdown代码块\n"
                "2. 每项字段：content（事项内容）、owner（负责人，无法确定填null）、deadline（截止时间，无法确定填null）\n"
                "3. 尽量提取，至少输出1项；确实没有任何行动项时才返回 []\n\n"
                "示例输出：\n"
                '[{{"content": "完成需求文档", "owner": "张三", "deadline": "本周五"}}, '
                '{{"content": "联系供应商", "owner": null, "deadline": null}}]\n\n'
                "会议内容：\n{text}\n\n"
                "待办事项JSON："
            )
            # 提取类任务固定 temperature=0，保证 JSON 输出稳定
            chain = prompt | self.llm.bind(temperature=0) | StrOutputParser()

            if len(text) <= settings.LLM_MAP_THRESHOLD_CHARS:
                result = await chain.ainvoke({"text": text})
                result = self._clean_json_output(result)
                todos = json.loads(result)
                return todos if isinstance(todos, list) else []

            chunks = self._chunk_text(text)
            if not chunks:
                return []

            print(f"[LLM] 长文本待办分段提取：{len(chunks)} 段")
            merged: List[Dict[str, Any]] = []
            seen = set()

            for index, chunk in enumerate(chunks, start=1):
                try:
                    result = await chain.ainvoke({"text": chunk})
                    result = self._clean_json_output(result)
                    todos = json.loads(result)
                    if not isinstance(todos, list):
                        continue

                    for todo in todos:
                        if not isinstance(todo, dict):
                            continue

                        content = str(todo.get("content") or "").strip()
                        if not content:
                            continue

                        key = re.sub(r"\s+", "", content)
                        if key in seen:
                            continue

                        seen.add(key)
                        merged.append({
                            "content": content,
                            "owner": todo.get("owner"),
                            "deadline": todo.get("deadline"),
                        })
                except Exception as e:
                    print(f"[LLM] 第 {index} 段待办提取失败: {e}")
                    continue

            return merged[:50]

        except Exception as e:
            print(f"[LLM] 提取待办事项失败: {e}")
            return []

    # ==================== 发言人总结 ====================

    async def _generate_speaker_summary(self, speakers_text: Dict[str, str]) -> Dict[str, str]:
        """生成发言人总结（单个发言人发言过长时分段汇总）"""
        speaker_summary: Dict[str, str] = {}

        base_prompt = PromptTemplate.from_template(
            "请用一句话总结以下发言人在会议中的主要观点和贡献（50字以内）：\n\n"
            "{text}\n\n"
            "总结："
        )
        base_chain = base_prompt | self.llm | StrOutputParser()

        partial_prompt = PromptTemplate.from_template(
            "以下是同一发言人在会议中某一段的发言内容。请用50字以内概括这段发言的要点：\n\n"
            "{text}\n\n"
            "要点："
        )
        partial_chain = partial_prompt | self.llm | StrOutputParser()

        final_prompt = PromptTemplate.from_template(
            "以下是同一发言人在会议不同阶段的要点。请综合成一句50字以内的最终总结：\n\n"
            "{text}\n\n"
            "总结："
        )
        final_chain = final_prompt | self.llm | StrOutputParser()

        for speaker_id, text in speakers_text.items():
            try:
                if len(text) <= settings.LLM_MAP_THRESHOLD_CHARS:
                    summary = await base_chain.ainvoke({"text": text})
                    speaker_summary[speaker_id] = summary.strip()
                    continue

                chunks = self._chunk_text(text)
                print(f"[LLM] 发言人 {speaker_id} 长发言分段总结：{len(chunks)} 段")

                partials: List[str] = []
                for index, chunk in enumerate(chunks, start=1):
                    try:
                        partial = await partial_chain.ainvoke({"text": chunk})
                        if partial.strip():
                            partials.append(partial.strip())
                    except Exception as e:
                        print(f"[LLM] 发言人 {speaker_id} 第 {index} 段总结失败: {e}")

                if not partials:
                    speaker_summary[speaker_id] = ""
                    continue

                if len(partials) == 1:
                    speaker_summary[speaker_id] = partials[0]
                    continue

                combined = "\n".join(partials)
                summary = await final_chain.ainvoke({"text": combined})
                speaker_summary[speaker_id] = summary.strip()

            except Exception as e:
                print(f"[LLM] 生成发言人 {speaker_id} 总结失败: {e}")
                speaker_summary[speaker_id] = ""

        return speaker_summary

    # ==================== 工具 ====================

    @staticmethod
    def _clean_json_output(text: str) -> str:
        """
        清洗 LLM 输出的 JSON

        - 去除 ```json ... ``` 代码块围栏
        - 模型偶尔会在 JSON 前后附加解释文字，这里从第一个 [ 或 { 开始
          用 raw_decode 提取第一个合法 JSON，避免整段解析失败
        """
        cleaned = text.strip()

        # 去除 ```json ... ``` 或 ``` ... ```
        cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
        cleaned = re.sub(r'\s*```$', '', cleaned)

        decoder = json.JSONDecoder()
        for index, char in enumerate(cleaned):
            if char in "[{":
                try:
                    obj, _ = decoder.raw_decode(cleaned[index:])
                    return json.dumps(obj, ensure_ascii=False)
                except json.JSONDecodeError:
                    continue

        return cleaned.strip()

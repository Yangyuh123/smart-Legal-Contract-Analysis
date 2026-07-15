"""合同生成服务 - 支持多轮对话的合同起草和修改."""
from __future__ import annotations

import logging
import json
from typing import List, Dict, Any, Optional, AsyncGenerator

from app.services.llm_client import get_llm_client
from app.utils.prompt_templates import (
    GENERATION_SYSTEM_PROMPT,
    format_generation_prompt,
    GENERATION_CONVERSATION_PROMPT_TEMPLATE,
)

logger = logging.getLogger(__name__)

# 对话历史最大轮次（保留最近N轮）
MAX_CONVERSATION_TURNS = 10


class GenerationService:
    """合同生成与多轮修改服务."""

    def __init__(self):
        self.llm = get_llm_client()
        # 存储对话上下文（生产环境应使用Redis）
        self._conversations: Dict[str, List[Dict[str, str]]] = {}

    async def generate(
        self,
        contract_type: str,
        requirements: str,
        party_a: str = "甲方",
        party_b: str = "乙方",
        special_clauses: Optional[List[str]] = None,
        template_style: str = "standard",
    ) -> str:
        """
        生成一份完整的合同。

        Args:
            contract_type: 合同类型
            requirements: 合同需求描述
            party_a: 甲方名称
            party_b: 乙方名称
            special_clauses: 特殊条款列表
            template_style: 模板风格

        Returns:
            完整的合同文本（Markdown格式）
        """
        special_clauses_text = "\n".join(f"- {c}" for c in special_clauses) if special_clauses else "无"

        user_prompt = format_generation_prompt(
            contract_type=contract_type,
            requirements=requirements,
            party_a=party_a,
            party_b=party_b,
            special_clauses=special_clauses_text,
            template_style=template_style,
        )

        messages = [
            {"role": "system", "content": GENERATION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        logger.info(f"Generating contract: type={contract_type}, style={template_style}")

        try:
            response = self.llm.chat_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=8192,
            )
            contract_text = response.get("content", "")
            logger.info(f"Contract generated: {len(contract_text)} chars")
            return contract_text
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise RuntimeError(f"合同生成失败: {e}")

    async def generate_stream(
        self,
        contract_type: str,
        requirements: str,
        conversation: Optional[List[Dict[str, str]]] = None,
        party_a: str = "甲方",
        party_b: str = "乙方",
        session_id: Optional[str] = None,
    ):
        """
        流式生成合同（支持多轮对话修改）。

        Args:
            contract_type: 合同类型
            requirements: 当前需求
            conversation: 多轮对话历史
            party_a: 甲方
            party_b: 乙方
            session_id: 会话ID

        Yields:
            str: SSE消息块
        """
        import uuid

        sid = session_id or str(uuid.uuid4())

        # 初始生成
        if not conversation:
            # RAG检索：从知识库获取相关合同模板/法律要求
            rag_context = ""
            try:
                from app.rag.retriever import get_retriever
                retriever = get_retriever()
                rag_query = f"{contract_type} {requirements} 合同条款"
                rag_context = retriever.retrieve_with_context(rag_query, top_k=3)
                if rag_context and "未找到" not in rag_context:
                    rag_context = "\n## 知识库参考资料\n" + rag_context
            except Exception as e:
                logger.warning(f"RAG检索失败(不影响生成): {e}")

            user_prompt = format_generation_prompt(
                contract_type=contract_type,
                requirements=requirements,
                party_a=party_a,
                party_b=party_b,
            )
            system_with_rag = GENERATION_SYSTEM_PROMPT + rag_context
            messages = [
                {"role": "system", "content": system_with_rag},
                {"role": "user", "content": user_prompt},
            ]
        else:
            # 多轮对话模式
            conversation_history = self._format_conversation(conversation)

            user_prompt = GENERATION_CONVERSATION_PROMPT_TEMPLATE.format(
                conversation_history=conversation_history,
                latest_message=requirements,
            )
            messages = [
                {"role": "system", "content": GENERATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]

        logger.info(f"Stream generation: session={sid}, messages={len(messages)}")

        # 流式输出
        try:
            for chunk in self.llm.chat_completion_stream(
                messages=messages,
                temperature=0.3,
                max_tokens=8192,
            ):
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"

            # 发送结束标记
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Stream generation error: {e}")
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    async def modify_contract(
        self,
        current_contract: str,
        modification_request: str,
    ) -> str:
        """
        根据修改要求对现有合同进行修改。

        Args:
            current_contract: 当前合同文本
            modification_request: 修改要求

        Returns:
            修改后的合同文本
        """
        messages = [
            {"role": "system", "content": GENERATION_SYSTEM_PROMPT},
            {"role": "user", "content": f"""以下是当前的合同文本：

{current_contract}

请根据以下要求修改合同（只输出修改后的完整合同，不要只输出修改部分）：

修改要求：{modification_request}"""},
        ]

        try:
            response = self.llm.chat_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=8192,
            )
            return response.get("content", "")
        except Exception as e:
            logger.error(f"Contract modification failed: {e}")
            raise RuntimeError(f"合同修改失败: {e}")

    def _format_conversation(self, conversation: List[Dict[str, str]]) -> str:
        """格式化对话历史."""
        if not conversation:
            return "无历史对话"

        # 只保留最近的消息
        recent = conversation[-MAX_CONVERSATION_TURNS * 2:]

        lines = []
        for msg in recent:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            role_name = "用户" if role == "user" else "AI助手"
            # 对于assistant的消息，截断显示
            if role == "assistant" and len(content) > 500:
                content = content[:500] + "...[合同内容已截断]"
            lines.append(f"{role_name}: {content}")

        return "\n\n".join(lines)

    async def _async_sleep(self, seconds: float):
        """异步睡眠."""
        import asyncio
        await asyncio.sleep(seconds)

    def clear_conversation(self, session_id: str):
        """清除指定会话的对话历史."""
        if session_id in self._conversations:
            del self._conversations[session_id]
            logger.info(f"Conversation cleared: {session_id}")

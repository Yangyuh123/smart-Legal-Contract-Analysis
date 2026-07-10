"""合同比较服务 - 对比两个合同版本，识别差异并评估法律风险."""
from __future__ import annotations

import logging
import time
import uuid
from typing import List, Dict, Any, Optional

from app.models.enums import DiffType
from app.models.schemas import CompareRequest, CompareResponse, DiffItem
from app.services.llm_client import get_llm_client
from app.utils.prompt_templates import (
    COMPARISON_SYSTEM_PROMPT,
    format_comparison_prompt,
)

logger = logging.getLogger(__name__)


class ComparisonService:
    """合同版本比较服务 - 文本差异分析 + AI法律影响评估."""

    def __init__(self):
        self.llm = get_llm_client()

    async def compare(self, request: CompareRequest) -> CompareResponse:
        """
        对比两份合同，找出所有差异并评估法律影响。

        Args:
            request: 比较请求

        Returns:
            比较结果

        Raises:
            ValueError: 输入无效
            RuntimeError: 处理失败
        """
        start_time = time.time()

        # 验证输入
        if not request.original_text or len(request.original_text.strip()) < 10:
            raise ValueError("原始合同文本过短")
        if not request.revised_text or len(request.revised_text.strip()) < 10:
            raise ValueError("修订合同文本过短")

        # 截断过长文本
        from app.parsers.text_cleaner import truncate_text
        max_len = 12000
        original_text = truncate_text(request.original_text, max_len)
        revised_text = truncate_text(request.revised_text, max_len)

        compare_mode = request.compare_mode or "detailed"
        review_requirements = request.review_requirements or "无额外要求"

        # 构建提示词
        user_prompt = format_comparison_prompt(
            original_text=original_text,
            revised_text=revised_text,
            compare_mode=compare_mode,
            review_requirements=review_requirements,
        )

        messages = [
            {"role": "system", "content": COMPARISON_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        logger.info(f"Starting comparison: mode={compare_mode}")

        # 调用LLM
        try:
            response = self.llm.chat_completion_structured(
                messages=messages,
                temperature=0.1,
                max_tokens=4096,
            )
        except ValueError as e:
            logger.error(f"LLM returned invalid JSON: {e}")
            raise RuntimeError(f"AI比较分析响应解析失败: {e}")
        except Exception as e:
            logger.error(f"Comparison LLM call failed: {e}")
            raise RuntimeError(f"AI比较服务调用失败: {e}")

        parsed = response.get("parsed", {})

        # 构建差异项
        diff_items = []
        raw_diffs = parsed.get("diffs", [])

        for item in raw_diffs:
            diff_type_str = item.get("diff_type", "modification").lower()
            # 规范化差异类型
            if diff_type_str not in ("addition", "deletion", "modification"):
                diff_type_str = "modification"

            diff_item = DiffItem(
                diff_type=DiffType(diff_type_str),
                clause_location=item.get("clause_location"),
                original_content=item.get("original_content"),
                revised_content=item.get("revised_content"),
                change_description=item.get("change_description", ""),
                risk_impact=item.get("risk_impact"),
            )
            diff_items.append(diff_item)

        # 计算文本相似度: 2*M/T*100 (difflib公式)
        import difflib
        sm = difflib.SequenceMatcher(None, original_text, revised_text)
        similarity = round(sm.ratio() * 100, 2)

        compare_time = round(time.time() - start_time, 2)

        response_obj = CompareResponse(
            compare_id=str(uuid.uuid4()),
            summary=parsed.get("summary", "比较完成"),
            similarity=similarity,
            total_diffs=len(diff_items),
            diffs=diff_items,
            risk_assessment=parsed.get("risk_assessment"),
        )

        logger.info(
            f"Comparison completed: id={response_obj.compare_id}, "
            f"similarity={similarity}%, diffs={response_obj.total_diffs}, time={compare_time}s"
        )

        return response_obj

    def text_diff(self, original: str, revised: str) -> List[Dict[str, Any]]:
        """
        纯文本级别差异检测（不依赖LLM），基于行级比较。

        Args:
            original: 原始文本
            revised: 修订文本

        Returns:
            差异列表 [{type: "addition"|"deletion"|"modification", "line": N, "content": str}, ...]
        """
        import difflib

        original_lines = original.split("\n")
        revised_lines = revised.split("\n")

        diffs = []
        matcher = difflib.SequenceMatcher(None, original_lines, revised_lines)

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue
            elif tag == "delete":
                for i in range(i1, i2):
                    diffs.append({
                        "type": "deletion",
                        "original_line": i + 1,
                        "content": original_lines[i],
                    })
            elif tag == "insert":
                for j in range(j1, j2):
                    diffs.append({
                        "type": "addition",
                        "revised_line": j + 1,
                        "content": revised_lines[j],
                    })
            elif tag == "replace":
                # 标记为修改：同时记录原始和修订内容
                old_content = "\n".join(original_lines[i1:i2])
                new_content = "\n".join(revised_lines[j1:j2])
                diffs.append({
                    "type": "modification",
                    "original_line_start": i1 + 1,
                    "original_line_end": i2,
                    "revised_line_start": j1 + 1,
                    "revised_line_end": j2,
                    "original_content": old_content,
                    "revised_content": new_content,
                })

        return diffs

    async def compare_quick(
        self,
        original_text: str,
        revised_text: str,
    ) -> Dict[str, Any]:
        """
        快速比较模式 - 结合文本diff和简要AI分析。

        Args:
            original_text: 原始文本
            revised_text: 修订文本

        Returns:
            简要比较结果
        """
        # 先做文本diff检测
        text_diffs = self.text_diff(original_text, revised_text)

        # 调用AI做简要分析
        request = CompareRequest(
            original_text=original_text,
            revised_text=revised_text,
            compare_mode="summary",
        )
        response = await self.compare(request)

        return {
            "compare_id": response.compare_id,
            "text_diffs_count": len(text_diffs),
            "ai_diffs_count": response.total_diffs,
            "text_diffs": text_diffs[:20],  # 只返回前20条文本差异
            "summary": response.summary,
            "risk_assessment": response.risk_assessment,
        }

"""合同审查服务 - 完整的合同法律风险审查流程."""
from __future__ import annotations

import logging
import time
import uuid
from typing import List, Dict, Any, Optional

from app.models.enums import RiskLevel, ReviewStatus
from app.models.schemas import ReviewRequest, ReviewResponse, RiskItem
from app.services.llm_client import get_llm_client
from app.utils.prompt_templates import (
    REVIEW_SYSTEM_PROMPT,
    format_review_prompt,
)

logger = logging.getLogger(__name__)


class ReviewService:
    """合同法律风险审查服务."""

    def __init__(self):
        self.llm = get_llm_client()

    async def review(self, request: ReviewRequest) -> ReviewResponse:
        """
        对合同进行全面法律风险审查。

        Args:
            request: 审查请求

        Returns:
            审查结果

        Raises:
            ValueError: 输入参数无效
            RuntimeError: LLM调用失败
        """
        start_time = time.time()

        # 验证输入
        if not request.contract_text or len(request.contract_text.strip()) < 10:
            raise ValueError("合同文本内容过短，请提供完整的合同文本（至少10个字符）")

        # 截断过长文本
        contract_text = request.contract_text
        if len(contract_text) > 15000:
            logger.warning(f"Contract text too long ({len(contract_text)} chars), truncating to 15000")
            from app.parsers.text_cleaner import truncate_text
            contract_text = truncate_text(contract_text, 15000)

        # 处理参数
        contract_type = request.contract_type or "未指定"
        party_context = request.party_context or "未提供"
        focus_areas = "、".join(request.focus_areas) if request.focus_areas else "全面审查"
        review_requirements = request.review_requirements or "无额外要求"

        # 构建提示词
        user_prompt = format_review_prompt(
            contract_text=contract_text,
            contract_type=contract_type,
            party_context=party_context,
            focus_areas=focus_areas,
            review_requirements=review_requirements,
        )

        messages = [
            {"role": "system", "content": REVIEW_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        # 调用LLM
        logger.info(f"Starting contract review: type={contract_type}, text_length={len(contract_text)}")

        try:
            response = self.llm.chat_completion_structured(
                messages=messages,
                model=None,  # Use default
                temperature=0.1,
                max_tokens=4096,
            )
        except ValueError as e:
            logger.error(f"LLM returned invalid JSON: {e}")
            raise RuntimeError(f"AI审查响应解析失败: {e}")
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise RuntimeError(f"AI审查服务调用失败: {e}")

        parsed = response.get("parsed", {})

        # 构建风险项列表
        risk_items = []
        risk_summary = {"CRITICAL": 0, "GENERAL": 0, "LOW": 0}

        raw_risks = parsed.get("risk_items", [])
        for item in raw_risks:
            risk_level_str = item.get("risk_level", "GENERAL").upper()
            # 规范风险等级
            if risk_level_str not in ("CRITICAL", "GENERAL", "LOW"):
                risk_level_str = "GENERAL"

            risk_item = RiskItem(
                risk_level=RiskLevel(risk_level_str),
                risk_category=item.get("risk_category", "未分类"),
                clause_location=item.get("clause_location"),
                original_text=item.get("original_text", ""),
                risk_description=item.get("risk_description", ""),
                suggestion=item.get("suggestion", ""),
                suggested_text=item.get("suggested_text"),
                legal_basis=item.get("legal_basis"),
            )
            risk_items.append(risk_item)
            risk_summary[risk_level_str] += 1

        # 计算审查耗时
        review_time = round(time.time() - start_time, 2)

        # 构建响应
        response_obj = ReviewResponse(
            review_id=str(uuid.uuid4()),
            status=ReviewStatus.COMPLETED,
            contract_type=parsed.get("contract_type", contract_type),
            overall_assessment=parsed.get("overall_assessment", "审查完成"),
            risk_summary=risk_summary,
            risk_items=risk_items,
            positive_points=parsed.get("positive_points"),
            review_time=review_time,
        )

        logger.info(
            f"Review completed: id={response_obj.review_id}, "
            f"risks={sum(risk_summary.values())}, "
            f"time={review_time}s"
        )

        return response_obj

    async def review_quick(self, contract_text: str, focus: Optional[str] = None) -> Dict[str, Any]:
        """
        快速审查模式 - 仅返回高风险项和简要评估（适合预览场景）。

        Args:
            contract_text: 合同文本
            focus: 重点关注领域

        Returns:
            简化版审查结果
        """
        request = ReviewRequest(
            contract_text=contract_text,
            contract_type=None,
            focus_areas=[focus] if focus else None,
            review_requirements="请重点关注CRITICAL级别的严重风险，简要列出即可。",
        )
        response = await self.review(request)

        # 简化为字典格式
        critical_risks = [r for r in response.risk_items if r.risk_level == RiskLevel.CRITICAL]

        return {
            "review_id": response.review_id,
            "contract_type": response.contract_type,
            "overall_assessment": response.overall_assessment,
            "critical_risks_count": len(critical_risks),
            "total_risks_count": len(response.risk_items),
            "critical_risks": [
                {
                    "category": r.risk_category,
                    "description": r.risk_description,
                    "suggestion": r.suggestion,
                }
                for r in critical_risks
            ],
            "positive_points": response.positive_points,
        }

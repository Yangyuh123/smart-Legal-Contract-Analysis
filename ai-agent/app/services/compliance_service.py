from __future__ import annotations
import logging
import time
import uuid
from typing import List, Dict, Any, Optional

from app.services.llm_client import get_llm_client
from app.utils.prompt_templates import (
    COMPLIANCE_SYSTEM_PROMPT,
    COMPLIANCE_USER_PROMPT_TEMPLATE,
)

logger = logging.getLogger(__name__)


class ComplianceService:
    """合同合规性审查服务."""

    def __init__(self):
        self.llm = get_llm_client()
    
    async def check(
        self,
        contract_text: str,
        compliance_standard: str,
        industry: str = "未指定",
        jurisdiction: str = "中国大陆",
        knowledge_context: str = "",
    ) -> Dict[str, Any]:
        """
        对合同文本进行合规性审查。

        Args:
            contract_text: 合同文本内容
            compliance_standard: 合规标准（如 "GDPR"、"数据安全法"）
            industry: 行业领域
            jurisdiction: 司法管辖区
            knowledge_context: 知识库参考资料（可选）

        Returns:
            合规审查结果字典

        Raises:
            ValueError: 输入参数无效
            RuntimeError: LLM调用失败
        """
        start_time = time.time()
        
        # 1. 验证输入
        if not contract_text or len(contract_text.strip()) < 10:
            raise ValueError("合同文本内容过短，请提供完整的合同文本（至少10个字符）")
        if not compliance_standard or len(compliance_standard.strip()) < 2:
            raise ValueError("合规标准不能为空")
        
        # 1.1 截断过长文本
        contract_text_truncated = contract_text
        if len(contract_text) > 15000:
            logger.warning(f"Contract text too long ({len(contract_text)} chars), truncating to 15000")
            from app.parsers.text_cleaner import truncate_text
            contract_text_truncated = truncate_text(contract_text, 15000)
        
        # 2. 构建提示词
        user_prompt = COMPLIANCE_USER_PROMPT_TEMPLATE.format(
        contract_text=contract_text_truncated,
        compliance_standard=compliance_standard,
        industry=industry,
        jurisdiction=jurisdiction,
        knowledge_context=knowledge_context,
    )
        
        messages = [
            {"role": "system", "content": COMPLIANCE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
        
        logger.info(f"Starting compliance check: standard={compliance_standard}, industry={industry}")
        
        # 3. 调用LLM
        try:
            response = self.llm.chat_completion_structured(
                messages=messages,
                temperature=0.1,
                max_tokens=4096,
            )
        except ValueError as e:
            logger.error(f"LLM returned invalid JSON: {e}")
            raise RuntimeError(f"AI合规审查响应解析失败: {e}")
        except Exception as e:
            logger.error(f"Compliance check LLM call failed: {e}")
            raise RuntimeError(f"AI合规审查服务调用失败: {e}")
        
        # 4. 解析返回的JSON
        parsed = response.get("parsed", {})
        
        # 5. 返回结构化结果
        result = {
            "check_id": str(uuid.uuid4()),
            "compliance_standard": compliance_standard,
            "industry": industry,
            "jurisdiction": jurisdiction,
            "overall_compliance": parsed.get("overall_compliance", "unknown"),
            "summary": parsed.get("summary", "合规审查完成"),
            "issues": parsed.get("issues", []),
            "compliant_items": parsed.get("compliant_items", []),
            "recommendations": parsed.get("recommendations", []),
            "check_time": round(time.time() - start_time, 2),
        }
        
        issue_counts = {"CRITICAL": 0, "GENERAL": 0, "LOW": 0}
        for issue in result["issues"]:
            severity = issue.get("severity", "GENERAL").upper()
            if severity in issue_counts:
                issue_counts[severity] += 1
        result["issue_counts"] = issue_counts
        result["total_issues"] = sum(issue_counts.values())
        
        logger.info(
            f"Compliance check completed: id={result['check_id']}, "
            f"overall={result['overall_compliance']}, "
            f"issues={result['total_issues']}, time={result['check_time']}s"
        )
        
        return result
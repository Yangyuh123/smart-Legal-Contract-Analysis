"""合同审查API路由."""
import logging
import traceback
from typing import Optional
from fastapi import APIRouter, HTTPException

from app.models.schemas import ReviewRequest, ReviewResponse, APIResponse
from app.services.review_service import ReviewService

logger = logging.getLogger(__name__)

router = APIRouter()
_review_service: Optional[ReviewService] = None


def get_review_service() -> ReviewService:
    global _review_service
    if _review_service is None:
        _review_service = ReviewService()
    return _review_service


@router.post("", response_model=APIResponse, summary="合同法律风险审查")
async def review_contract(request: ReviewRequest):
    """
    对合同文本进行全面的法律风险审查。

    审查维度包括：
    - 主体资格与签约权限
    - 价款与支付条款
    - 交付与验收标准
    - 知识产权条款
    - 保密条款
    - 违约责任
    - 争议解决
    - 不可抗力等

    返回按严重程度分类的风险列表，每条风险包含：
    - 风险等级（CRITICAL/GENERAL/LOW）
    - 风险说明
    - 原文引用
    - 修改建议
    - 法律依据
    """
    try:
        result = await get_review_service().review(request)
        return APIResponse(
            code=200,
            message="审查完成",
            data=result.model_dump(),
        )
    except ValueError as e:
        logger.warning(f"Invalid review request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Review service error: {e}")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected review error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"审查服务内部错误: {str(e)}")


@router.post("/quick", response_model=APIResponse, summary="快速合同审查（预览）")
async def review_contract_quick(request: ReviewRequest):
    """
    快速审查模式 - 仅返回关键风险项和简要评估。
    适用于合同上传后的即时预览反馈。
    """
    try:
        result = await get_review_service().review_quick(
            contract_text=request.contract_text,
            focus=request.focus_areas[0] if request.focus_areas else None,
        )
        return APIResponse(
            code=200,
            message="快速审查完成",
            data=result,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Quick review error: {e}")
        raise HTTPException(status_code=500, detail=f"快速审查失败: {str(e)}")

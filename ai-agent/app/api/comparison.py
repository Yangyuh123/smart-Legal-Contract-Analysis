"""合同比较API路由."""
import logging
import traceback
from typing import Optional
from fastapi import APIRouter, HTTPException

from app.models.schemas import CompareRequest, CompareResponse, APIResponse
from app.services.comparison_service import ComparisonService

logger = logging.getLogger(__name__)

router = APIRouter()
_comparison_service: Optional[ComparisonService] = None


def get_comparison_service() -> ComparisonService:
    global _comparison_service
    if _comparison_service is None:
        _comparison_service = ComparisonService()
    return _comparison_service


@router.post("", response_model=APIResponse, summary="合同版本比较")
async def compare_contracts(request: CompareRequest):
    """
    对比两份合同（原始版本与修订版本），找出所有差异并评估法律影响。

    支持三种比较模式：
    - **detailed**: 详细比较，逐条列出所有变更及其法律风险影响
    - **summary**: 摘要比较，仅列出关键差异和整体评估
    - **risks_only**: 仅列出可能增加法律风险的变更

    每处差异包含：
    - 差异类型（新增/删除/修改）
    - 条款位置
    - 原始内容和修订内容
    - 变更描述
    - 法律风险影响评估
    """
    try:
        result = await get_comparison_service().compare(request)
        return APIResponse(
            code=200,
            message="比较完成",
            data=result.model_dump(),
        )
    except ValueError as e:
        logger.warning(f"Invalid comparison request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Comparison service error: {e}")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected comparison error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"合同比较服务内部错误: {str(e)}")


@router.post("/quick", response_model=APIResponse, summary="快速合同比较")
async def compare_contracts_quick(request: CompareRequest):
    """
    快速比较模式 - 结合文本级diff检测和AI简要分析。
    适用于快速了解两个合同版本的关键差异。
    """
    try:
        result = await get_comparison_service().compare_quick(
            original_text=request.original_text,
            revised_text=request.revised_text,
        )
        return APIResponse(
            code=200,
            message="快速比较完成",
            data=result,
        )
    except Exception as e:
        logger.error(f"Quick comparison error: {e}")
        raise HTTPException(status_code=500, detail=f"快速比较失败: {str(e)}")

from fastapi import APIRouter, HTTPException
import logging
from typing import Optional

from app.models.schemas import APIResponse, ComplianceRequest
from app.services.compliance_service import ComplianceService

logger = logging.getLogger(__name__)
router = APIRouter()

_compliance_service: Optional[ComplianceService] = None


def get_compliance_service() -> ComplianceService:
    global _compliance_service
    if _compliance_service is None:
        _compliance_service = ComplianceService()
    return _compliance_service


@router.post("", response_model=APIResponse, summary="合同合规性检查")
async def check_compliance(request: ComplianceRequest):
    try:
        result = await get_compliance_service().check(
            contract_text=request.contract_text,
            compliance_standard=request.compliance_standard,
            industry=request.industry,
            jurisdiction=request.jurisdiction,
        )
        return APIResponse(code=200, message="合规检查完成", data=result)
    except ValueError as e:
        logger.warning(f"Invalid compliance request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Compliance service error: {e}")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected compliance error: {e}")
        raise HTTPException(status_code=500, detail=f"合规检查服务内部错误: {str(e)}")
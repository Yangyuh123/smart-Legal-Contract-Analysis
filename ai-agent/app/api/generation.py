"""合同生成API路由 - 支持SSE流式输出和多轮对话."""
import json
import logging
import traceback
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.models.schemas import GenerateStreamRequest, APIResponse
from app.services.generation_service import GenerationService

logger = logging.getLogger(__name__)

router = APIRouter()
_generation_service: Optional[GenerationService] = None


def get_generation_service() -> GenerationService:
    global _generation_service
    if _generation_service is None:
        _generation_service = GenerationService()
    return _generation_service


@router.post("/stream", summary="流式生成合同（SSE）")
async def generate_contract_stream(request: GenerateStreamRequest):
    """
    流式生成/修改合同，支持多轮对话。

    使用Server-Sent Events (SSE) 协议推送生成内容：
    - {"type": "session", "session_id": "..."}  - 会话信息
    - {"type": "content", "data": "..."}         - 合同文本块
    - {"type": "done", "session_id": "..."}      - 生成完成
    - {"type": "error", "message": "..."}        - 错误信息

    首轮调用：不传conversation参数，系统会生成初始合同。
    后续调用：传入conversation对话历史，系统会根据要求修改合同。
    """
    try:
        return StreamingResponse(
            get_generation_service().generate_stream(
                contract_type=request.contract_type,
                requirements=request.requirements,
                conversation=request.conversation,
                party_a=request.party_a or "甲方",
                party_b=request.party_b or "乙方",
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except Exception as e:
        logger.error(f"Stream generation error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"合同生成失败: {str(e)}")


@router.post("", response_model=APIResponse, summary="生成合同（非流式）")
async def generate_contract(request: GenerateStreamRequest):
    """
    一次性生成完整合同（非流式）。
    适用于不需要实时展示生成过程的场景。
    """
    try:
        contract_text = await get_generation_service().generate(
            contract_type=request.contract_type,
            requirements=request.requirements,
            party_a=request.party_a or "甲方",
            party_b=request.party_b or "乙方",
        )
        return APIResponse(
            code=200,
            message="合同生成完成",
            data={
                "contract_type": request.contract_type,
                "contract_text": contract_text,
                "format": "markdown",
            },
        )
    except Exception as e:
        logger.error(f"Contract generation error: {e}")
        raise HTTPException(status_code=500, detail=f"合同生成失败: {str(e)}")


class ModifyRequest(BaseModel):
    """合同修改请求."""
    current_contract: str = Field(..., description="当前合同文本")
    modification_request: str = Field(..., description="修改要求")


@router.post("/modify", response_model=APIResponse, summary="修改已有合同")
async def modify_contract(request: ModifyRequest):
    """
    根据修改要求对已有合同进行修改。

    请求体示例：
    ```json
    {
      "current_contract": "第一条...\\n第二条...",
      "modification_request": "请在违约责任条款中增加违约金上限为合同总额30%的约定"
    }
    ```
    """
    try:
        modified = await get_generation_service().modify_contract(
            current_contract=request.current_contract,
            modification_request=request.modification_request,
        )
        return APIResponse(
            code=200,
            message="合同修改完成",
            data={"contract_text": modified},
        )
    except Exception as e:
        logger.error(f"Contract modification error: {e}")
        raise HTTPException(status_code=500, detail=f"合同修改失败: {str(e)}")

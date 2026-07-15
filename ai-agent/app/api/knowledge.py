"""知识库问答API路由 - 支持流式问答和文档索引."""
import logging
import traceback
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.models.schemas import KnowledgeQARequest, KnowledgeIndexRequest, APIResponse
from app.services.knowledge_service import KnowledgeService

logger = logging.getLogger(__name__)

router = APIRouter()
_knowledge_service: Optional[KnowledgeService] = None


def get_knowledge_service() -> KnowledgeService:
    global _knowledge_service
    if _knowledge_service is None:
        _knowledge_service = KnowledgeService()
    return _knowledge_service


@router.post("/qa", summary="知识库流式问答（SSE）")
async def knowledge_qa_stream(request: KnowledgeQARequest):
    """
    基于RAG的知识库流式问答。

    使用SSE协议推送回答内容：
    - {"type": "content", "data": "..."}  - 回答文本块
    - {"type": "done"}                    - 回答完成
    - {"type": "error", "message": "..."} - 错误信息
    """
    try:
        return StreamingResponse(
            get_knowledge_service().qa_stream(
                question=request.question,
                conversation_history=request.conversation_history,
                top_k=request.top_k,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except Exception as e:
        logger.error(f"Knowledge QA stream error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"知识库问答失败: {str(e)}")


class QASyncRequest(BaseModel):
    """非流式问答请求."""
    question: str = Field(..., description="问题")
    top_k: int = Field(default=5, ge=1, le=20, description="检索文档数")


@router.post("/qa/sync", response_model=APIResponse, summary="知识库问答（非流式）")
async def knowledge_qa_sync(request: QASyncRequest):
    """非流式知识库问答 - 一次性返回完整回答."""
    try:
        result = await get_knowledge_service().qa(
            question=request.question,
            top_k=request.top_k,
        )
        return APIResponse(
            code=200,
            message="问答完成",
            data=result,
        )
    except Exception as e:
        logger.error(f"QA sync error: {e}")
        raise HTTPException(status_code=500, detail=f"知识库问答失败: {str(e)}")


@router.post("/index", response_model=APIResponse, summary="索引文件到知识库")
async def index_knowledge(request: KnowledgeIndexRequest):
    """
    将文件索引入知识库，用于后续RAG检索。

    支持格式：.pdf, .docx, .txt, .md

    索引流程：
    1. 加载并解析文件内容
    2. 使用法律条款分割器进行语义分块
    3. 生成向量嵌入（本地 sentence-transformers 模型，如 BGE-zh）
    4. 存入ChromaDB向量数据库
    5. 同步构建BM25稀疏检索索引
    """
    try:
        result = await get_knowledge_service().index_files(
            file_paths=request.file_paths,
            collection_name=request.collection_name,
            chunk_size=request.chunk_size or 800,
            chunk_overlap=request.chunk_overlap or 100,
        )
        return APIResponse(
            code=200,
            message=f"索引完成，共索引{result.get('chunks_indexed', 0)}个文本块",
            data=result,
        )
    except Exception as e:
        logger.error(f"Indexing error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"知识库索引失败: {str(e)}")


@router.post("/search", response_model=APIResponse, summary="搜索知识库")
async def search_knowledge(request: QASyncRequest):
    """搜索知识库（仅检索，不生成回答），返回相关度最高的法律知识片段."""
    try:
        results = await get_knowledge_service().search_knowledge(
            query=request.question,
            top_k=request.top_k,
        )
        return APIResponse(
            code=200,
            message=f"找到{len(results)}条相关结果",
            data={
                "query": request.question,
                "total": len(results),
                "results": results,
            },
        )
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"知识库搜索失败: {str(e)}")


@router.delete("/index", response_model=APIResponse, summary="删除知识库索引")
async def delete_knowledge(file_name: str = Query(..., description="要删除的文件名")):
    """从知识库中删除指定文件的索引."""
    try:
        result = await get_knowledge_service().delete_knowledge(file_name=file_name)
        return APIResponse(
            code=200,
            message=f"已删除{result.get('deleted_chunks', 0)}个索引块",
            data=result,
        )
    except Exception as e:
        logger.error(f"Delete knowledge error: {e}")
        raise HTTPException(status_code=500, detail=f"删除知识库索引失败: {str(e)}")

"""API路由聚合器 - 汇集所有子路由到统一的API路由实例."""
from fastapi import APIRouter

from app.api.review import router as review_router
from app.api.generation import router as generation_router
from app.api.comparison import router as comparison_router
from app.api.knowledge import router as knowledge_router
from app.api.parse import router as parse_router
from app.api.compliance import router as compliance_router
api_router = APIRouter()

api_router.include_router(review_router, prefix="/review", tags=["合同审查"])
api_router.include_router(generation_router, prefix="/generate", tags=["合同生成"])
api_router.include_router(comparison_router, prefix="/compare", tags=["合同比较"])
api_router.include_router(knowledge_router, prefix="/knowledge", tags=["知识库"])
api_router.include_router(parse_router, prefix="/parse", tags=["文档解析"])
api_router.include_router(compliance_router, prefix="/compliance", tags=["合规检查"])

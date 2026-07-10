"""Pydantic schemas for SmartLegal AI Agent API."""
from __future__ import annotations

from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.enums import RiskLevel, DiffType, ReviewStatus


# ──────────────────────────────────────────────
# 通用响应模型
# ──────────────────────────────────────────────

class APIResponse(BaseModel):
    """统一API响应格式."""
    code: int = Field(default=200, description="状态码")
    message: str = Field(default="success", description="响应消息")
    data: Optional[Any] = Field(default=None, description="响应数据")


# ──────────────────────────────────────────────
# 文档解析
# ──────────────────────────────────────────────

class ParseRequest(BaseModel):
    """文档解析请求 - 上传合同文件进行内容提取."""
    file_name: str = Field(..., description="文件名（含扩展名）")
    file_content: Optional[str] = Field(default=None, description="文件内容的Base64编码（与file_url二选一）")
    file_url: Optional[str] = Field(default=None, description="文件URL路径（与file_content二选一）")
    parse_options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="解析选项，如 {'extract_tables': True, 'extract_clauses': True}"
    )


class ParseResponse(BaseModel):
    """文档解析响应."""
    file_name: str = Field(..., description="解析的文件名")
    full_text: str = Field(..., description="提取的完整文本内容")
    page_count: int = Field(default=0, description="文档页数（PDF适用）")
    clauses: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="提取的条款列表，每项包含 {clause_no, title, content}"
    )
    tables: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="提取的表格数据"
    )
    parse_time: float = Field(default=0.0, description="解析耗时（秒）")


# ──────────────────────────────────────────────
# 合同审查
# ──────────────────────────────────────────────

class ReviewRequest(BaseModel):
    """合同审查请求."""
    contract_text: str = Field(..., description="待审查的合同文本内容", min_length=10)
    contract_type: Optional[str] = Field(
        default=None,
        description="合同类型，如：采购合同、劳动合同、租赁合同、保密协议等"
    )
    focus_areas: Optional[List[str]] = Field(
        default=None,
        description="重点关注领域，如 ['违约责任', '知识产权', '保密条款', '争议解决']"
    )
    party_context: Optional[str] = Field(
        default=None,
        description="当事人背景信息，如 '我方为乙方/供应商'"
    )
    review_requirements: Optional[str] = Field(
        default=None,
        description="额外的审查要求或关注点"
    )


class RiskItem(BaseModel):
    """合同风险项."""
    risk_level: RiskLevel = Field(..., description="风险等级：CRITICAL/GENERAL/LOW")
    risk_category: str = Field(..., description="风险类别，如：违约责任、知识产权、付款条款")
    clause_location: Optional[str] = Field(default=None, description="风险所在条款位置描述")
    original_text: str = Field(..., description="原始条款文本")
    risk_description: str = Field(..., description="风险说明：为什么存在风险")
    suggestion: str = Field(..., description="修改建议文本")
    suggested_text: Optional[str] = Field(default=None, description="建议替换的条款文本（可选）")
    legal_basis: Optional[str] = Field(default=None, description="法律依据，引用相关法规")


class ReviewResponse(BaseModel):
    """合同审查响应."""
    review_id: str = Field(..., description="审查任务ID")
    status: ReviewStatus = Field(default=ReviewStatus.COMPLETED, description="审查状态")
    contract_type: Optional[str] = Field(default=None, description="识别的合同类型")
    overall_assessment: str = Field(..., description="整体评估意见")
    risk_summary: Dict[str, int] = Field(
        default_factory=dict,
        description="风险统计摘要，如 {'CRITICAL': 3, 'GENERAL': 5, 'LOW': 2}"
    )
    risk_items: List[RiskItem] = Field(default_factory=list, description="风险项列表")
    positive_points: Optional[List[str]] = Field(
        default=None,
        description="合同中的合规/优势条款"
    )
    review_time: float = Field(default=0.0, description="审查耗时（秒）")


# ──────────────────────────────────────────────
# 合同生成
# ──────────────────────────────────────────────

class GenerateRequest(BaseModel):
    """合同生成请求."""
    contract_type: str = Field(..., description="合同类型，如：采购合同、劳动合同")
    requirements: str = Field(..., description="合同需求描述，包括关键条款和条件")
    party_a: Optional[str] = Field(default="甲方", description="甲方名称")
    party_b: Optional[str] = Field(default="乙方", description="乙方名称")
    special_clauses: Optional[List[str]] = Field(
        default=None,
        description="需要特别加入的条款列表"
    )
    template_style: Optional[str] = Field(
        default="standard",
        description="模板风格：standard-标准法律文书, simple-简明版, detailed-详细版"
    )


class GenerateStreamRequest(BaseModel):
    """合同生成流式请求（支持多轮对话修改）."""
    contract_type: str = Field(..., description="合同类型")
    requirements: str = Field(..., description="初始合同需求描述")
    conversation: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description="多轮对话历史 [{'role': 'user'/'assistant', 'content': '...'}]"
    )
    party_a: Optional[str] = Field(default="甲方", description="甲方名称")
    party_b: Optional[str] = Field(default="乙方", description="乙方名称")


# ──────────────────────────────────────────────
# 合同比较
# ──────────────────────────────────────────────

class CompareRequest(BaseModel):
    """合同比较请求."""
    original_text: str = Field(..., description="原始合同文本（作为比较基准）", min_length=10)
    revised_text: str = Field(..., description="修订后的合同文本", min_length=10)
    compare_mode: Optional[str] = Field(
        default="detailed",
        description="比较模式：detailed-详细比较, summary-摘要比较, risks_only-仅比较风险差异"
    )
    review_requirements: Optional[str] = Field(
        default=None,
        description="审查要求或关注重点，作为AI比对的额外依据"
    )


class DiffItem(BaseModel):
    """合同差异项."""
    diff_type: DiffType = Field(..., description="差异类型：addition/deletion/modification")
    clause_location: Optional[str] = Field(default=None, description="差异所在条款位置")
    original_content: Optional[str] = Field(default=None, description="原始内容（deletion/modification时提供）")
    revised_content: Optional[str] = Field(default=None, description="修订内容（addition/modification时提供）")
    change_description: str = Field(..., description="变更描述说明")
    risk_impact: Optional[str] = Field(
        default=None,
        description="变更对法律风险的影响评估"
    )


class CompareResponse(BaseModel):
    """合同比较响应."""
    compare_id: str = Field(..., description="比较任务ID")
    summary: str = Field(..., description="比较结果摘要")
    similarity: float = Field(default=0.0, description="文本相似度 0-100")
    total_diffs: int = Field(..., description="差异总数")
    diffs: List[DiffItem] = Field(default_factory=list, description="差异项列表")
    risk_assessment: Optional[str] = Field(default=None, description="整体风险评估")


# ──────────────────────────────────────────────
# 知识库问答
# ──────────────────────────────────────────────

class KnowledgeQuery(BaseModel):
    """知识库检索查询."""
    query: str = Field(..., description="查询问题", min_length=1)
    top_k: int = Field(default=5, ge=1, le=20, description="返回相关文档数量")
    filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="过滤条件，如 {'doc_type': 'law', 'category': 'contract_law'}"
    )


class KnowledgeQARequest(BaseModel):
    """知识库问答请求（支持流式输出）."""
    question: str = Field(..., description="用户问题", min_length=1)
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description="对话历史"
    )
    top_k: int = Field(default=5, ge=1, le=20, description="检索相关文档数量")
    stream: bool = Field(default=True, description="是否使用SSE流式输出")


class KnowledgeIndexRequest(BaseModel):
    """知识库索引请求."""
    file_paths: List[str] = Field(..., description="待索引的文件路径列表")
    collection_name: Optional[str] = Field(default="legal_knowledge", description="向量库集合名称")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="附加元数据，如: {\"source\": \"civil_code\", \"version\": \"2021\"}"
    )
    chunk_size: Optional[int] = Field(default=800, description="文本分块大小")
    chunk_overlap: Optional[int] = Field(default=100, description="分块重叠大小")

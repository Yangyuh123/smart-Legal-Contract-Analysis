"""Enumerations for the SmartLegal AI Agent."""
from enum import Enum


class RiskLevel(str, Enum):
    """风险等级枚举 - 合同审查中的风险严重程度分类."""
    CRITICAL = "CRITICAL"  # 严重风险：可能导致重大法律后果或经济损失
    GENERAL = "GENERAL"    # 一般风险：存在一定法律瑕疵，建议修改
    LOW = "LOW"            # 低风险：表述可优化，无实质法律风险


class DiffType(str, Enum):
    """差异类型枚举 - 合同比较中的变更类型."""
    ADDITION = "addition"        # 新增内容
    DELETION = "deletion"        # 删除内容
    MODIFICATION = "modification"  # 修改内容


class ReviewStatus(str, Enum):
    """审查状态枚举 - 合同审查任务的生命周期状态."""
    PENDING = "PENDING"        # 待处理
    PROCESSING = "PROCESSING"  # 审查中
    COMPLETED = "COMPLETED"    # 已完成
    FAILED = "FAILED"          # 审查失败

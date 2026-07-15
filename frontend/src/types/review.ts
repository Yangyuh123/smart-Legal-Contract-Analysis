/**
 * 合同审查相关类型定义
 */

/** 风险等级 */
export enum RiskLevel {
  /** 高风险 */
  HIGH = 'HIGH',
  /** 中风险 */
  MEDIUM = 'MEDIUM',
  /** 低风险 */
  LOW = 'LOW',
}

/** 审查状态 */
export enum ReviewStatus {
  /** 待审查 */
  PENDING = 'PENDING',
  /** 审查中 */
  PROCESSING = 'PROCESSING',
  /** 已完成 */
  COMPLETED = 'COMPLETED',
  /** 审查失败 */
  FAILED = 'FAILED',
}

/** 审查发现的风险项 */
export interface ReviewRisk {
  /** 风险项 ID */
  id: string
  /** 所属审查记录 ID */
  reviewId: string
  /** 风险标题 / 名称 */
  title: string
  /** 风险描述 */
  description: string
  /** 风险等级 */
  riskLevel: RiskLevel
  /** 风险所在位置描述，格式如 "第3页 第2段" */
  location: string
  /** 合同原文 */
  originalText: string
  /** 修改建议 */
  suggestion: string
  /** 相关法规条款引用 */
  relatedClause: string
  /** 是否已忽略该风险 */
  isIgnored: boolean
}

/** 审查记录 */
export interface ReviewRecord {
  /** 审查记录 ID */
  id: string
  /** 关联合同 ID */
  contractId: string
  /** 关联合同标题 */
  contractTitle: string
  /** 审查状态 */
  status: ReviewStatus
  /** 审查发现的风险列表 */
  risks: ReviewRisk[]
  /** 审查总结 */
  summary: string
  /** 修改建议列表 */
  suggestions: string[]
  /** 合同评分（0-100） */
  score: number
  /** 创建时间 */
  createTime: string
  /** 最近更新时间 */
  updateTime: string
  /** 审查人 ID */
  reviewerId: string
}

/** 风险概要统计 */
export interface RiskSummary {
  /** 高风险数量 */
  highCount: number
  /** 中风险数量 */
  mediumCount: number
  /** 低风险数量 */
  lowCount: number
  /** 风险总数 */
  totalCount: number
  /** 整体评分（0-100） */
  overallScore: number
  /** 整体风险等级 */
  overallLevel: RiskLevel
}

/** 审查请求参数 */
export interface ReviewRequest {
  /** 待审查合同 ID */
  contractId: string
  /** 审查类型（如：全面审查 / 专项审查） */
  reviewType?: string
  /** 自定义审查要点 */
  checkPoints?: string[]
}

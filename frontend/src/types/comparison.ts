/**
 * 合同比对相关类型定义（与后端 ComparisonResultVO 对齐）
 */

/** 差异项 */
export interface DiffItem {
  diffType: 'addition' | 'deletion' | 'modification'
  clauseSection?: string
  contentA?: string
  contentB?: string
  summary?: string
}

/** 比对记录 */
export interface ComparisonResult {
  id: number
  similarity: number
  additions: number
  deletions: number
  modifications: number
  diffs: DiffItem[]
  createTime: string
}

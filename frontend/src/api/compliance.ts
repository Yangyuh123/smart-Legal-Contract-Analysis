import { get, post } from './index'

export type Severity = 'CRITICAL' | 'GENERAL' | 'LOW'

export interface ComplianceIssue {
  id: number
  issueTitle: string
  severity: Severity
  clauseReference: string
  description: string
  legalReference: string
  recommendation: string
  penaltyRisk: string
}

export interface ComplianceRecord {
  id: number
  fileName: string
  complianceStandard: string
  industry: string
  jurisdiction: string
  overallCompliance: string
  summary: string
  totalIssues: number
  criticalIssues: number
  generalIssues: number
  lowIssues: number
  issues?: ComplianceIssue[]
  createTime: string
}

export interface PageData<T> {
  records: T[]
  total: number
  page: number
  size: number
}

export interface ComplianceUploadResult {
  id: number
}

export const complianceApi = {
  list(params: { page: number; size: number }): Promise<PageData<ComplianceRecord>> {
    return get('/compliance', params as any)
  },
  getById(id: number): Promise<ComplianceRecord> {
    return get(`/compliance/${id}`)
  },
  upload(data: FormData): Promise<ComplianceUploadResult> {
    return post('/compliance/upload', data)
  },
}
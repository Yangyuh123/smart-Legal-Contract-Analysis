import { get, post } from './index'

export type RiskLevel = 'CRITICAL' | 'GENERAL' | 'LOW'

export interface ReviewRisk {
  id: number; reviewId: number; riskLevel: RiskLevel; riskCategory: string
  riskTitle: string; riskDescription: string; riskPosition: string
  clauseSection: string; suggestion: string; suggestedText: string; legalBasis: string
}

export interface ReviewRecord {
  id: number; fileName?: string; contractTitle?: string; status: string
  totalRisks: number; criticalRisks: number; generalRisks: number; lowRisks: number
  reviewSummary: string; createTime: string; risks?: ReviewRisk[]
}

export interface PageData<T> { records: T[]; total: number; page: number; size: number }

export const reviewApi = {
  list(params: { page: number; size: number }): Promise<PageData<ReviewRecord>> {
    return get('/reviews', params as any)
  },
  getById(id: number): Promise<ReviewRecord> {
    return get(`/reviews/${id}`)
  },
  getStats(): Promise<any> {
    return get('/reviews/stats')
  },
}

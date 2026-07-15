import { get, post } from './index'

export interface ComparisonResult {
  id: number
  similarity: number
  additions: number
  deletions: number
  modifications: number
  diffs: any[]
  createTime: string
}

export interface PageData<T> { records: T[]; total: number; page: number; size: number }

export const comparisonApi = {
  /** 比对列表 */
  list(params: { page: number; size: number }): Promise<PageData<ComparisonResult>> {
    return get('/comparisons', params as any)
  },
  /** 比对详情 */
  getById(id: number): Promise<ComparisonResult> {
    return get(`/comparisons/${id}`)
  },
  /** 上传两份文件发起比对 (直接用 fetch，因为返回可能是 SSE 或长耗时) */
  upload(fileA: File, fileB: File): Promise<any> {
    const fd = new FormData()
    fd.append('fileA', fileA)
    fd.append('fileB', fileB)
    return post('/comparisons/upload', fd)
  },
}

import { get, post, del } from './index'

export const knowledgeApi = {
  uploadDoc(data: FormData): Promise<any> {
    return post('/knowledge/documents', data)
  },
  listDocs(params: { page: number; size: number }): Promise<{ records: any[]; total: number }> {
    return get('/knowledge/documents', params as any)
  },
  deleteDoc(id: number): Promise<void> {
    return del(`/knowledge/documents/${id}`)
  },
}

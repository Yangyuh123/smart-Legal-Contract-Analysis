/**
 * 知识库相关类型定义（与后端 kb_document 表 / KbDocument 实体对齐）
 */

/** 知识库文档 */
export interface KnowledgeDocument {
  id: number
  title: string
  content: string
  category: string
  tags: string
  source: string
  vectorId: string
  chunkCount: number
  status: number
  createTime: string
  updateTime: string
}

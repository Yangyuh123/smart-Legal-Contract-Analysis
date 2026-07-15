/**
 * 合同生成相关类型定义
 *
 * 后端仅提供 SSE 流式接口 POST /api/v1/generation/stream
 * 无会话/消息持久化，前端 GenerationChatView 直接用 fetch 调用。
 */

/** 合同类型 */
export type ContractType =
  | '买卖合同'
  | '租赁合同'
  | '劳动合同'
  | '保密协议'
  | '服务合同'
  | '合作协议'
  | '借款合同'
  | '其他'

/** 生成请求参数（POST /generation/stream body） */
export interface GenerationRequest {
  contractType: string
  requirements: string
  partyA: string
  partyB: string
}

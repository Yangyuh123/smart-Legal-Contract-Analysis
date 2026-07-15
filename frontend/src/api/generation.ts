/**
 * AI 合同生成 API
 *
 * 后端 GenerationController: POST /api/v1/generation/stream (SSE)
 * 前端 GenerationChatView 直接使用 fetch 调用 SSE 接口，
 * 此文件仅保留最小导出供需要时引用。
 */

// 合同生成目前无 REST CRUD 接口，仅有 SSE 流式接口。
// GenerationChatView.vue 已直接用 fetch 调用 /api/v1/generation/stream
export const generationApi = {}

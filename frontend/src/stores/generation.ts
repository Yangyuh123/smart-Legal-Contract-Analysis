import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * 合同生成 Store
 *
 * 后端仅提供 SSE 流式接口，无会话持久化。
 * GenerationChatView 直接使用 fetch 调用 SSE，
 * 此 Store 仅保留 UI 状态管理。
 */
export const useGenerationStore = defineStore('generation', () => {
  const streaming = ref(false)
  const generatedContent = ref('')

  function setStreaming(val: boolean) { streaming.value = val }
  function setContent(val: string) { generatedContent.value = val }
  function appendContent(chunk: string) { generatedContent.value += chunk }
  function clearContent() { generatedContent.value = '' }

  return { streaming, generatedContent, setStreaming, setContent, appendContent, clearContent }
})

import { ref, onUnmounted } from 'vue'

/**
 * Server-Sent Events (SSE) 流式请求组合式函数
 *
 * 基于 fetch ReadableStream 实现流式内容读取，按 SSE 协议解析
 * "data: ...\n\n" 格式的 chunk，逐步累积到 streamContent 中，
 * 适用于 AI 对话/审查结果等需要逐字/逐 token 展示的场景。
 *
 * @example
 * ```ts
 * const { isStreaming, streamContent, error, startStream, stopStream } = useSSE()
 * startStream('/api/review/stream/123', {
 *   onMessage: (token) => { /* 自定义处理 *\/ },
 *   onComplete: () => { /* 流结束 *\/ },
 * })
 * ```
 */
export function useSSE() {
  const isStreaming = ref(false)
  const streamContent = ref('')
  const error = ref<string | null>(null)

  let abortController: AbortController | null = null

  // ---- 流式启动 ----

  interface SSECallbacks {
    /** 每条 SSE data 消息的回调（已去除 data: 前缀），若未提供则拼接至 streamContent */
    onMessage?: (token: string) => void
    /** 流错误回调 */
    onError?: (err: Error) => void
    /** 流正常结束回调 */
    onComplete?: () => void
  }

  /**
   * 发起 SSE 流式请求
   * @param url       SSE 端点
   * @param options   可选的请求头和回调
   */
  async function startStream(
    url: string,
    options?: {
      headers?: Record<string, string>
      callbacks?: SSECallbacks
    },
  ): Promise<void> {
    // 如果已有进行中的流，先停止
    if (isStreaming.value) {
      stopStream()
    }

    isStreaming.value = true
    streamContent.value = ''
    error.value = null

    abortController = new AbortController()

    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          Accept: 'text/event-stream',
          ...options?.headers,
        },
        signal: abortController.signal,
      })

      if (!response.ok) {
        throw new Error(`SSE 连接失败: HTTP ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('浏览器不支持 ReadableStream')
      }

      const decoder = new TextDecoder('utf-8')
      let buffer = ''

      // eslint-disable-next-line no-constant-condition
      while (true) {
        const { done, value } = await reader.read()

        if (done) {
          // 流自然结束
          isStreaming.value = false
          options?.callbacks?.onComplete?.()
          return
        }

        // 解码 chunk 并追加到缓冲区
        buffer += decoder.decode(value, { stream: true })

        // 按行解析 SSE 格式
        const lines = buffer.split('\n')
        // 最后一个元素可能是不完整的行，保留到下次循环
        buffer = lines.pop() || ''

        for (const line of lines) {
          const trimmed = line.trim()

          // 空行（SSE 事件分隔符）— 表示一条完整消息结束
          if (trimmed === '') continue

          if (trimmed.startsWith('data:')) {
            const data = trimmed.slice(5).trim()

            // SSE 规范：data: [DONE] 表示流结束（OpenAI 风格）
            if (data === '[DONE]') {
              isStreaming.value = false
              options?.callbacks?.onComplete?.()
              return
            }

            // 累加到 streamContent
            streamContent.value += data
            options?.callbacks?.onMessage?.(data)
          }
          // 忽略 event: / id: / retry: 等 SSE 字段（当前无需使用）
        }
      }
    } catch (err: any) {
      // AbortError 由 stopStream 触发，属于正常终止
      if (err.name === 'AbortError') {
        isStreaming.value = false
        return
      }

      const wrapped = err instanceof Error ? err : new Error(String(err))
      error.value = wrapped.message
      isStreaming.value = false
      options?.callbacks?.onError?.(wrapped)
    }
  }

  // ---- 流式停止 ----

  /** 中止当前 SSE 连接 */
  function stopStream(): void {
    if (abortController) {
      abortController.abort()
      abortController = null
    }
    isStreaming.value = false
  }

  // ---- 生命周期清理 ----
  onUnmounted(() => {
    stopStream()
  })

  // ---- expose ----
  return {
    isStreaming,
    streamContent,
    error,
    startStream,
    stopStream,
  }
}

import { reactive, ref, computed, watch } from 'vue'

/**
 * 通用分页组合式函数
 *
 * 将分页状态（页码、每页条数、总数）与异步数据获取函数绑定，
 * 允许外部调用 refresh / reset 主动刷新，并通过 watch 自动感知
 * page / pageSize 的变化以重新拉取数据。
 *
 * @param fetchFn  接收 { page, pageSize } 并返回 Promise 的异步函数，
 *                 返回值应包含 { records, total }（或兼容结构）。
 * @param defaultPageSize  默认每页条数，默认 10
 *
 * @example
 * ```ts
 * const { state, loading, handlePageChange, handleSizeChange, refresh, reset } =
 *   usePagination(params => contractApi.list({ ...params, ...filters }), 10)
 * ```
 */
export function usePagination(
  fetchFn: (params: { page: number; pageSize: number }) => Promise<{
    data: { records: any[]; total: number }
  }>,
  defaultPageSize = 10,
) {
  const state = reactive({
    page: 1,
    pageSize: defaultPageSize,
    total: 0,
  })

  const loading = ref(false)
  const data = ref<any[]>([])
  const error = ref<string | null>(null)

  /** 标志：是否允许自动触发（reset 时会短暂关闭，防止重复请求） */
  let autoFetchEnabled = true

  // ---- 核心：执行数据获取 ----

  async function execute(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const res = await fetchFn({
        page: state.page,
        pageSize: state.pageSize,
      })
      data.value = res.data.records ?? []
      state.total = res.data.total ?? 0
    } catch (err: any) {
      const msg = err?.response?.data?.message || err?.message || '数据加载失败'
      error.value = msg
    } finally {
      loading.value = false
    }
  }

  // ---- 分页事件处理 ----

  /** Element Plus 分页组件的 current-change 事件 */
  function handlePageChange(page: number): void {
    state.page = page
  }

  /** Element Plus 分页组件的 size-change 事件 */
  function handleSizeChange(size: number): void {
    state.pageSize = size
    // pageSize 变化时通常需要回到第一页
    state.page = 1
  }

  /** 刷新当前页数据（保持页码不变） */
  function refresh(): void {
    execute()
  }

  /** 回到第一页并重新加载 */
  function reset(): void {
    autoFetchEnabled = false
    state.page = 1
    state.total = 0
    data.value = []
    autoFetchEnabled = true
    execute()
  }

  // ---- 自动触发：page / pageSize 变化时重新获取 ----

  watch([() => state.page, () => state.pageSize], () => {
    if (!autoFetchEnabled) return
    execute()
  })

  // ---- 首次加载 ----
  execute()

  // ---- expose ----
  return {
    state,
    loading,
    data,
    error,
    handlePageChange,
    handleSizeChange,
    refresh,
    reset,
  }
}

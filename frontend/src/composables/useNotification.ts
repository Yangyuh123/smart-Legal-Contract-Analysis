import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useNotificationStore } from '@/stores/notification'
import { useAuthStore } from '@/stores/auth'

/**
 * 通知轮询组合式函数
 *
 * 在组件中挂载时自动开始轮询未读通知数量（仅在已登录时），
 * 卸载时自动清理定时器，避免手动管理生命周期。
 *
 * @param options           可选配置
 * @param options.pollInterval  轮询间隔（毫秒），默认 30000（30 秒）
 * @param options.autoPoll      是否自动开始轮询，默认 true
 *
 * @example
 * ```ts
 * const { unreadCount, notifications, startPolling, stopPolling, fetchNotifications } =
 *   useNotification({ pollInterval: 15000 })
 * ```
 */
export function useNotification(options?: {
  pollInterval?: number
  autoPoll?: boolean
}) {
  const pollInterval = options?.pollInterval ?? 30000
  const autoPoll = options?.autoPoll ?? true

  const store = useNotificationStore()
  const authStore = useAuthStore()

  let timer: ReturnType<typeof setInterval> | null = null
  const polling = ref(false)

  // ---- 轮询控制 ----

  /** 开始轮询未读数量 */
  function startPolling(intervalMs?: number): void {
    // 未登录时不轮询
    if (!authStore.isAuthenticated) return

    stopPolling() // 防止重复定时器

    const ms = intervalMs ?? pollInterval
    polling.value = true

    // 立即拉取一次
    store.fetchUnreadCount()

    timer = setInterval(() => {
      if (!authStore.isAuthenticated) {
        stopPolling()
        return
      }
      store.fetchUnreadCount()
    }, ms)
  }

  /** 停止轮询 */
  function stopPolling(): void {
    polling.value = false
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  // ---- 生命周期 ----

  onMounted(() => {
    if (autoPoll && authStore.isAuthenticated) {
      startPolling()
    }
  })

  onUnmounted(() => {
    stopPolling()
  })

  // ---- 派生状态（从 store 直接映射） ----

  const unreadCount = computed(() => store.unreadCount)
  const notifications = computed(() => store.notifications)
  const loading = computed(() => store.loading)
  const total = computed(() => store.total)

  // ---- expose ----
  return {
    // state
    unreadCount,
    notifications,
    loading,
    total,
    polling,
    // actions（透传 store 方法）
    fetchNotifications: store.fetchNotifications,
    markAsRead: store.markAsRead,
    markAllAsRead: store.markAllAsRead,
    // 轮询控制
    startPolling,
    stopPolling,
  }
}

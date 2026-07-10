import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Notification } from '@/types/notification'
import { notificationApi } from '@/api/notification'

export const useNotificationStore = defineStore('notification', () => {
  const notifications = ref<Notification[]>([])
  const unreadCount = ref(0)
  const loading = ref(false)
  const total = ref(0)

  let pollingTimer: ReturnType<typeof setInterval> | null = null
  const polling = ref(false)

  /** 获取通知列表 */
  async function fetchNotifications(params: { page?: number; size?: number } = {}): Promise<void> {
    loading.value = true
    try {
      const res = await notificationApi.list({
        page: params.page || 1,
        size: params.size || 20,
      })
      notifications.value = res.records
      total.value = res.total
    } finally {
      loading.value = false
    }
  }

  /** 获取未读数量 */
  async function fetchUnreadCount(): Promise<void> {
    try {
      const count = await notificationApi.unreadCount()
      unreadCount.value = count
    } catch {
      /* ignore */
    }
  }

  /** 标记单条为已读 */
  async function markAsRead(id: number | string): Promise<void> {
    await notificationApi.markRead(id)
    unreadCount.value = Math.max(0, unreadCount.value - 1)
    const target = notifications.value.find(n => n.id === Number(id))
    if (target) target.isRead = 1
  }

  /** 全部标记为已读 */
  async function markAllAsRead(): Promise<void> {
    await notificationApi.markAllRead()
    unreadCount.value = 0
    notifications.value.forEach(n => { n.isRead = 1 })
  }

  function incrementUnread(): void { unreadCount.value++ }
  function decrementUnread(): void { unreadCount.value = Math.max(0, unreadCount.value - 1) }

  function startPolling(intervalMs: number = 30000): void {
    if (polling.value) return
    polling.value = true
    fetchUnreadCount()
    pollingTimer = setInterval(() => {
      if (!polling.value) { stopPolling(); return }
      fetchUnreadCount()
    }, intervalMs)
  }

  function stopPolling(): void {
    polling.value = false
    if (pollingTimer) { clearInterval(pollingTimer); pollingTimer = null }
  }

  return {
    notifications, unreadCount, loading, total, polling,
    fetchNotifications, fetchUnreadCount, markAsRead, markAllAsRead,
    incrementUnread, decrementUnread, startPolling, stopPolling,
  }
})

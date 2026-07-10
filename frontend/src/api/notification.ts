import { get, put } from './index'

/** 通知消息（与后端 NotificationVO 对齐） */
export interface Notification {
  id: number
  userId: number
  title: string
  content: string
  /** 通知类型：review / compliance / system 等 */
  type: string
  /** 关联业务 ID */
  relatedId: number
  /** 是否已读 0-未读 1-已读 */
  isRead: number
  createTime: string
}

export interface PageData<T> { records: T[]; total: number; page: number; size: number }

export const notificationApi = {
  /** 通知分页列表 */
  list(params: { page: number; size: number }): Promise<PageData<Notification>> {
    return get('/notifications', params as any)
  },
  /** 未读通知数量 */
  unreadCount(): Promise<number> {
    return get('/notifications/unread-count')
  },
  /** 标记单条为已读 */
  markRead(id: number | string): Promise<void> {
    return put(`/notifications/${id}/read`)
  },
  /** 全部标记为已读 */
  markAllRead(): Promise<void> {
    return put('/notifications/read-all')
  },
}

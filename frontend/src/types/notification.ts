/**
 * 通知消息相关类型定义（与后端 NotificationVO 对齐）
 */

/** 通知消息 */
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

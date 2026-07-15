/**
 * Formatting utility functions for display values.
 *
 * All functions are pure, synchronous, and return strings or rich display
 * objects suitable for rendering in Vue templates.
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** Risk level enumeration used across the application. */
export type RiskLevel = 'CRITICAL' | 'GENERAL' | 'LOW'

/** Status values for async operations. */
export type ProcessStatus =
  | 'PENDING'
  | 'PROCESSING'
  | 'UPLOADING'
  | 'ANALYZING'
  | 'COMPLETED'
  | 'SUCCESS'
  | 'FAILED'
  | 'ERROR'
  | 'CANCELLED'
  | 'DRAFT'
  | 'PUBLISHED'
  | 'REVIEWING'
  | 'APPROVED'
  | 'REJECTED'
  | 'ARCHIVED'

// ---------------------------------------------------------------------------
// 1. Date Formatting
// ---------------------------------------------------------------------------

/**
 * Formats a date value to a display string.
 *
 * @param date  - A Date object, ISO string, timestamp, or date string.
 * @param fmt   - Format pattern. Supported tokens:
 *                YYYY, MM, DD, HH, mm, ss.
 *                Default: 'YYYY-MM-DD HH:mm:ss'.
 * @returns Formatted date string, or '--' for invalid input.
 */
export function formatDate(
  date: string | Date | number,
  fmt: string = 'YYYY-MM-DD HH:mm:ss',
): string {
  if (date === null || date === undefined || date === '') {
    return '--'
  }

  const d = new Date(date)

  if (isNaN(d.getTime())) {
    return '--'
  }

  const tokens: Record<string, string> = {
    YYYY: String(d.getFullYear()),
    MM: String(d.getMonth() + 1).padStart(2, '0'),
    DD: String(d.getDate()).padStart(2, '0'),
    HH: String(d.getHours()).padStart(2, '0'),
    mm: String(d.getMinutes()).padStart(2, '0'),
    ss: String(d.getSeconds()).padStart(2, '0'),
  }

  let result = fmt
  for (const [token, value] of Object.entries(tokens)) {
    result = result.replace(token, value)
  }
  return result
}

/**
 * Formats a date to a relative time string (Chinese).
 *
 * @param date - The date to format relative to now.
 * @returns Relative time string like "刚刚", "3分钟前", "2天前" etc.
 */
export function formatRelativeTime(date: string | Date | number): string {
  const now = Date.now()
  const then = new Date(date).getTime()

  if (isNaN(then)) return '--'

  const diff = now - then
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  const weeks = Math.floor(days / 7)
  const months = Math.floor(days / 30)
  const years = Math.floor(days / 365)

  if (seconds < 10) return '刚刚'
  if (seconds < 60) return `${seconds}秒前`
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days === 1) return '昨天'
  if (days === 2) return '前天'
  if (days < 7) return `${days}天前`
  if (weeks < 4) return `${weeks}周前`
  if (months < 12) return `${months}个月前`
  if (years < 2) return '1年前'
  return `${years}年前`
}

// ---------------------------------------------------------------------------
// 2. File Size Formatting
// ---------------------------------------------------------------------------

/**
 * Converts a byte count into a human-readable string.
 *
 * @param bytes - File size in bytes.
 * @returns Formatted string like "1.5 MB".
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  if (bytes < 0) return '0 B'
  if (!Number.isFinite(bytes)) return '--'

  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const k = 1024
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(k)), units.length - 1)
  const value = bytes / Math.pow(k, i)

  // Use fewer decimals for larger units
  const decimals = i === 0 ? 0 : value >= 100 ? 1 : 2
  return value.toFixed(decimals) + ' ' + units[i]
}

// ---------------------------------------------------------------------------
// 3. Risk Level Formatting
// ---------------------------------------------------------------------------

/** Display object returned by formatRiskLevel */
export interface RiskLevelDisplay {
  label: string
  color: string
  type: '' | 'success' | 'warning' | 'danger'
}

/**
 * Maps a RiskLevel enum value to display properties for UI rendering.
 *
 * @param level - The risk level code.
 * @returns An object with label (Chinese), color (hex), and type (Element Plus tag type).
 */
export function formatRiskLevel(level: RiskLevel | string): RiskLevelDisplay {
  const map: Record<string, RiskLevelDisplay> = {
    CRITICAL: { label: '重大风险', color: '#c01c28', type: 'danger' },
    HIGH: { label: '高风险', color: '#c01c28', type: 'danger' },
    GENERAL: { label: '一般风险', color: '#e5a50a', type: 'warning' },
    MEDIUM: { label: '中等风险', color: '#e5a50a', type: 'warning' },
    LOW: { label: '低风险', color: '#26a269', type: 'success' },
    NONE: { label: '无风险', color: '#909399', type: '' },
  }

  return (
    map[level] || { label: level || '--', color: '#909399', type: '' }
  )
}

// ---------------------------------------------------------------------------
// 4. Status Formatting
// ---------------------------------------------------------------------------

/** Display object returned by formatStatus */
export interface StatusDisplay {
  label: string
  color: string
  type: '' | 'success' | 'warning' | 'danger' | 'info' | 'primary'
}

/**
 * Maps a status string to a Chinese label and display color.
 *
 * @param status - A ProcessStatus or arbitrary status string.
 * @returns Display properties for the status.
 */
export function formatStatus(status: string): StatusDisplay {
  const map: Record<string, StatusDisplay> = {
    PENDING: { label: '待处理', color: '#e5a50a', type: 'warning' },
    PROCESSING: { label: '处理中', color: '#3584e4', type: 'info' },
    UPLOADING: { label: '上传中', color: '#3584e4', type: 'info' },
    ANALYZING: { label: '分析中', color: '#3584e4', type: 'info' },
    COMPLETED: { label: '已完成', color: '#26a269', type: 'success' },
    SUCCESS: { label: '成功', color: '#26a269', type: 'success' },
    FAILED: { label: '失败', color: '#c01c28', type: 'danger' },
    ERROR: { label: '异常', color: '#c01c28', type: 'danger' },
    CANCELLED: { label: '已取消', color: '#909399', type: 'info' },
    DRAFT: { label: '草稿', color: '#909399', type: 'info' },
    PUBLISHED: { label: '已发布', color: '#1a5fb4', type: 'primary' },
    REVIEWING: { label: '审核中', color: '#3584e4', type: 'info' },
    APPROVED: { label: '已通过', color: '#26a269', type: 'success' },
    REJECTED: { label: '已驳回', color: '#c01c28', type: 'danger' },
    ARCHIVED: { label: '已归档', color: '#909399', type: 'info' },
    ACTIVE: { label: '启用', color: '#26a269', type: 'success' },
    DISABLED: { label: '禁用', color: '#c01c28', type: 'danger' },
    INACTIVE: { label: '未激活', color: '#909399', type: 'info' },
    DELETED: { label: '已删除', color: '#c01c28', type: 'danger' },
  }

  return (
    map[status] || {
      label: status || '--',
      color: '#909399',
      type: 'info',
    }
  )
}

// ---------------------------------------------------------------------------
// 5. Number Formatting
// ---------------------------------------------------------------------------

/**
 * Formats a number with thousands separators.
 *
 * @param num - The number to format.
 * @returns Formatted string like "123,456,789".
 */
export function formatNumber(num: number): string {
  if (num === null || num === undefined || !Number.isFinite(num)) {
    return '--'
  }
  return num.toLocaleString('zh-CN')
}

/**
 * Formats a number as a percentage string.
 *
 * @param value    - The numeric value (e.g. 0.856 for 85.6%).
 * @param decimals - Number of decimal places (default: 1).
 * @returns Formatted percentage string like "85.6%".
 */
export function formatPercentage(value: number, decimals: number = 1): string {
  if (!Number.isFinite(value)) return '--'
  return (value * 100).toFixed(decimals) + '%'
}

// ---------------------------------------------------------------------------
// 6. Text Formatting
// ---------------------------------------------------------------------------

/**
 * Truncates text to a maximum length, appending an ellipsis if truncated.
 *
 * @param text      - The input text.
 * @param maxLength - Maximum character count before truncation.
 * @returns The truncated (or original) text.
 */
export function truncateText(text: string, maxLength: number): string {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + '...'
}

// ---------------------------------------------------------------------------
// 7. Money / Currency
// ---------------------------------------------------------------------------

/**
 * Formats a number as a Chinese Yuan (CNY) currency string.
 *
 * @param amount - The monetary amount.
 * @returns Formatted currency string like "¥1,234.56".
 */
export function formatMoney(amount: number): string {
  if (!Number.isFinite(amount)) return '--'
  return '¥' + amount.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

// ---------------------------------------------------------------------------
// 8. Duration
// ---------------------------------------------------------------------------

/**
 * Formats a duration in seconds to a human-readable string.
 *
 * @param seconds - Duration in seconds.
 * @returns String like "2小时30分钟".
 */
export function formatDuration(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return '--'

  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)

  const parts: string[] = []
  if (h > 0) parts.push(`${h}小时`)
  if (m > 0) parts.push(`${m}分钟`)
  if (s > 0 || parts.length === 0) parts.push(`${s}秒`)

  return parts.join('')
}

// ---------------------------------------------------------------------------
// 9. Phone / ID masking
// ---------------------------------------------------------------------------

/**
 * Masks the middle digits of a phone number.
 *
 * @param phone - The full phone number.
 * @returns Masked phone like "138****1234".
 */
export function maskPhone(phone: string): string {
  if (!phone || phone.length < 7) return phone || '--'
  return phone.slice(0, 3) + '****' + phone.slice(-4)
}

/**
 * Masks the middle portion of an ID number.
 *
 * @param idNumber - The full ID number.
 * @returns Masked ID like "3201**********1234".
 */
export function maskIdNumber(idNumber: string): string {
  if (!idNumber || idNumber.length < 8) return idNumber || '--'
  const head = idNumber.slice(0, 4)
  const tail = idNumber.slice(-4)
  const maskLen = idNumber.length - 8
  return head + '*'.repeat(Math.max(maskLen, 4)) + tail
}

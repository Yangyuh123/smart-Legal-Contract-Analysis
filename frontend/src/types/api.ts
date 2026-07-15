/**
 * API 通用响应类型定义
 */

/** 通用 API 响应包装 */
export interface ApiResponse<T = unknown> {
  /** 业务状态码，200 表示成功 */
  code: number
  /** 响应消息，成功或错误描述 */
  message: string
  /** 响应数据 */
  data: T
  /** 请求追踪 ID，用于日志排查 */
  traceId?: string
  /** 服务器时间戳 */
  timestamp?: number
}

/** 分页查询结果 */
export interface PageResult<T = unknown> {
  /** 当前页数据记录列表 */
  records: T[]
  /** 总记录数 */
  total: number
  /** 当前页码 */
  page: number
  /** 每页条数 */
  pageSize: number
  /** 总页数 */
  totalPages?: number
}

/** 分页查询请求参数 */
export interface PageRequest {
  /** 页码，从 1 开始 */
  page: number
  /** 每页条数 */
  pageSize: number
  /** 排序字段 */
  sortField?: string
  /** 排序方向：asc 升序，desc 降序 */
  sortOrder?: 'asc' | 'desc'
}

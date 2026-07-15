import axios from 'axios'
import type {
  AxiosInstance,
  InternalAxiosRequestConfig,
  AxiosResponse,
  AxiosError,
} from 'axios'
import { message } from '@/utils/feedback'
import router from '@/router'

/**
 * 创建 axios 实例
 *
 * - baseURL 优先读取环境变量 VITE_API_BASE_URL，回退为 '/api/v1'
 * - 默认超时 30 秒
 * - 默认 Content-Type 为 application/json
 */
const instance: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api/v1',
  timeout: 30000,
})

// ============================================================
// 请求拦截器 —— 自动附带 JWT Bearer Token
// ============================================================

instance.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error: AxiosError) => Promise.reject(error),
)

// ============================================================
// 响应拦截器 —— 统一错误处理
// ============================================================

instance.interceptors.response.use(
  (response: AxiosResponse) => {
    // 部分后端将业务错误包装在 HTTP 200 的 body 中
    const data = response.data
    if (data && typeof data.code === 'number' && data.code !== 0 && data.code !== 200) {
      message.error(data.message || '请求失败')
      return Promise.reject(new Error(data.message || '请求失败'))
    }
    return response
  },
  (error: AxiosError<{ message?: string }>) => {
    if (error.response) {
      const { status, data } = error.response
      switch (status) {
        case 401:
          // Token 过期或无效 —— 清除登录态并跳转登录页
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          if (router.currentRoute.value.path !== '/auth/login') {
            router.push('/auth/login').catch(() => {
              window.location.href = '/auth/login'
            })
          }
          message.error('登录已过期，请重新登录')
          break
        case 403:
          message.error(data?.message || '无访问权限')
          break
        case 500:
          message.error(data?.message || '服务器内部错误')
          break
        default:
          message.error(data?.message || `请求失败 (${status})`)
      }
    } else if (error.code === 'ECONNABORTED') {
      message.error('请求超时，请稍后重试')
    } else if (!window.navigator.onLine) {
      message.error('网络已断开，请检查网络连接')
    } else {
      message.error('网络异常，请稍后重试')
    }
    return Promise.reject(error)
  },
)

/** 将 axios 实例作为默认导出，供各 API 模块使用 */
export default instance

// ============================================================
// 泛型请求助手 (命名导出)
// ============================================================

/**
 * 请求配置参数
 */
export interface RequestConfig {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  url: string
  params?: Record<string, any>
  data?: any
  headers?: Record<string, string>
  timeout?: number
  responseType?: 'json' | 'blob' | 'arraybuffer' | 'text'
}

/**
 * 泛型请求助手 —— 封装 axios 实例，直接返回反序列化后的数据类型
 *
 * @example
 * ```ts
 * import { request } from '@/api'
 *
 * const user = await request<UserInfo>({
 *   method: 'GET',
 *   url: '/auth/me',
 * })
 * ```
 */
export async function request<T = any>(config: RequestConfig): Promise<T> {
  const response = await instance.request<T>(config)
  return response.data
}

// ============================================================
// 便捷方法 — 自动提取 response.data.data
// ============================================================

function extract<T>(response: AxiosResponse<ApiResponse<T>>): T {
  return response.data.data
}

export type ApiResponse<T = any> = {
  code: number
  message: string
  data: T
}

export async function get<T = any>(url: string, params?: Record<string, any>): Promise<T> {
  const resp = await instance.get<ApiResponse<T>>(url, { params })
  return extract(resp)
}

export async function post<T = any>(url: string, data?: any): Promise<T> {
  const config: any = {}
  // FormData 需要 multipart，axios 会自
  if (data instanceof FormData) {
    config.headers = { 'Content-Type': 'multipart/form-data' }
  }
  const resp = await instance.post<ApiResponse<T>>(url, data, config)
  return extract(resp)
}

export async function put<T = any>(url: string, data?: any): Promise<T> {
  const resp = await instance.put<ApiResponse<T>>(url, data)
  return extract(resp)
}

export async function del<T = any>(url: string): Promise<T> {
  const resp = await instance.delete<ApiResponse<T>>(url)
  return extract(resp)
}

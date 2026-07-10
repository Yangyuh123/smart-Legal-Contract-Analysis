/**
 * Axios wrapper utility for making HTTP requests.
 *
 * Provides a pre-configured axios instance and typed helper functions
 * (get, post, put, del) that extract response data and support AbortSignal
 * for request cancellation.
 *
 * This is a generic utility — the project's domain-specific API layer
 * (src/api/index.ts) builds on top of these helpers.
 */

import axios, {
  type AxiosInstance,
  type AxiosRequestConfig,
  type AxiosResponse,
} from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'
import type { ApiResponse } from '@/types/api'

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

const instance: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ---------------------------------------------------------------------------
// Request Interceptor — attach JWT
// ---------------------------------------------------------------------------

instance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// ---------------------------------------------------------------------------
// Response Interceptor — unified error handling & data extraction
// ---------------------------------------------------------------------------

instance.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    const res = response.data
    if (res.code !== 200) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return response
  },
  (error) => {
    if (error.response) {
      const { status } = error.response
      switch (status) {
        case 401:
          localStorage.removeItem('token')
          localStorage.removeItem('refreshToken')
          localStorage.removeItem('user')
          router.push('/auth/login')
          ElMessage.error('登录已过期，请重新登录')
          break
        case 403:
          ElMessage.error('权限不足')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 500:
          ElMessage.error('服务器内部错误')
          break
        default:
          ElMessage.error(
            error.response.data?.message || '请求失败',
          )
      }
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时')
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }
    return Promise.reject(error)
  },
)

// ---------------------------------------------------------------------------
// Exported instance (for direct use when full response is needed)
// ---------------------------------------------------------------------------

export default instance

// ---------------------------------------------------------------------------
// Typed helpers — extract response.data.data
// ---------------------------------------------------------------------------

/**
 * Extracts the `data` property from the API response envelope.
 *
 * Assumes the backend wraps responses as:
 *   { code: 200, message: "ok", data: T }
 *
 * Use these helpers when you only care about the payload.
 */
function extractData<T>(response: AxiosResponse<ApiResponse<T>>): T {
  return response.data.data
}

/**
 * Performs a GET request.
 *
 * @param url     - Request URL (appended to baseURL).
 * @param params  - Query parameters.
 * @param signal  - Optional AbortSignal for cancellation.
 * @returns A promise resolving to the extracted response data of type T.
 */
export async function get<T = unknown>(
  url: string,
  params?: Record<string, unknown>,
  signal?: AbortSignal,
): Promise<T> {
  const resp = await instance.get<ApiResponse<T>>(url, { params, signal })
  return extractData(resp)
}

/**
 * Performs a POST request.
 *
 * @param url     - Request URL (appended to baseURL).
 * @param data    - Request body.
 * @param signal  - Optional AbortSignal for cancellation.
 * @returns A promise resolving to the extracted response data of type T.
 */
export async function post<T = unknown>(
  url: string,
  data?: unknown,
  signal?: AbortSignal,
): Promise<T> {
  const resp = await instance.post<ApiResponse<T>>(url, data, { signal })
  return extractData(resp)
}

/**
 * Performs a PUT request.
 *
 * @param url     - Request URL (appended to baseURL).
 * @param data    - Request body.
 * @param signal  - Optional AbortSignal for cancellation.
 * @returns A promise resolving to the extracted response data of type T.
 */
export async function put<T = unknown>(
  url: string,
  data?: unknown,
  signal?: AbortSignal,
): Promise<T> {
  const resp = await instance.put<ApiResponse<T>>(url, data, { signal })
  return extractData(resp)
}

/**
 * Performs a DELETE request.
 *
 * @param url     - Request URL (appended to baseURL).
 * @param signal  - Optional AbortSignal for cancellation.
 * @returns A promise resolving to the extracted response data of type T.
 */
export async function del<T = unknown>(
  url: string,
  signal?: AbortSignal,
): Promise<T> {
  const resp = await instance.delete<ApiResponse<T>>(url, { signal })
  return extractData(resp)
}

/**
 * Performs a PATCH request.
 *
 * @param url     - Request URL (appended to baseURL).
 * @param data    - Request body.
 * @param signal  - Optional AbortSignal for cancellation.
 * @returns A promise resolving to the extracted response data of type T.
 */
export async function patch<T = unknown>(
  url: string,
  data?: unknown,
  signal?: AbortSignal,
): Promise<T> {
  const resp = await instance.patch<ApiResponse<T>>(url, data, { signal })
  return extractData(resp)
}

/**
 * Uploads a file via POST with `multipart/form-data`.
 *
 * @param url     - Upload endpoint URL.
 * @param file    - The File object to upload.
 * @param fieldName - Form field name for the file (default: "file").
 * @param extraData - Additional form fields to include.
 * @param signal  - Optional AbortSignal.
 * @returns A promise resolving to the extracted response data.
 */
export async function upload<T = unknown>(
  url: string,
  file: File,
  fieldName: string = 'file',
  extraData?: Record<string, string>,
  signal?: AbortSignal,
): Promise<T> {
  const formData = new FormData()
  formData.append(fieldName, file)

  if (extraData) {
    Object.entries(extraData).forEach(([key, value]) => {
      formData.append(key, value)
    })
  }

  const resp = await instance.post<ApiResponse<T>>(url, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    signal,
  })
  return extractData(resp)
}

/**
 * Downloads a file via GET and returns the raw response (for blob downloads).
 *
 * @param url     - Download endpoint URL.
 * @param params  - Query parameters.
 * @param signal  - Optional AbortSignal.
 * @returns The full AxiosResponse with blob data.
 */
export async function downloadRaw(
  url: string,
  params?: Record<string, unknown>,
  signal?: AbortSignal,
): Promise<AxiosResponse<Blob>> {
  return instance.get(url, {
    params,
    signal,
    responseType: 'blob',
  })
}

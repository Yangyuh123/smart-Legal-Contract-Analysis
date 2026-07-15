import { post, get } from './index'
import type { UserInfo, LoginRequest, RegisterRequest } from '@/types/user'

export const authApi = {
  /** 登录 — 返回 {token, refreshToken, user} */
  login(data: LoginRequest): Promise<{ token: string; refreshToken: string; user: UserInfo }> {
    return post('/auth/login', data)
  },

  /** 注册 */
  register(data: RegisterRequest): Promise<null> {
    return post('/auth/register', data)
  },

  /** 刷新令牌 — 后端 @RequestParam，需要 query string */
  refreshToken(): Promise<{ token: string; refreshToken: string }> {
    const rt = localStorage.getItem('refresh_token')
    return post(`/auth/refresh?refreshToken=${encodeURIComponent(rt || '')}`)
  },

  /** 获取当前用户 */
  getCurrentUser(): Promise<UserInfo> {
    return get('/auth/me')
  },
}

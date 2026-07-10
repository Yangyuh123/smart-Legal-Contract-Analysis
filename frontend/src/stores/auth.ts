import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { LoginRequest, RegisterRequest } from '@/types/user'
import { authApi } from '@/api/auth'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<any>(null)
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(null)
  const permissions = ref<string[]>([])

  const isAuthenticated = computed(() => !!token.value)

  function restoreSession(): void {
    const storedToken = localStorage.getItem('access_token')
    const storedRefresh = localStorage.getItem('refresh_token')
    const storedUser = localStorage.getItem('user')

    if (storedToken) {
      token.value = storedToken
      refreshToken.value = storedRefresh || null
      if (storedUser) {
        try {
          user.value = JSON.parse(storedUser)
          permissions.value = user.value?.permissions || []
        } catch { /* ignore */ }
      }
      // 恢复会话时启动通知轮询
      import('@/stores/notification').then(m => m.useNotificationStore().startPolling())
    }
  }

  /** 登录 — res 已经是 extractData 后的 payload */
  async function login(credentials: LoginRequest): Promise<void> {
    const res: any = await authApi.login(credentials)
    // 后端返回: { token, refreshToken, user: {..., roles:[], permissions:[]} }
    const { token: accessToken, refreshToken: refresh, user: userInfo } = res

    token.value = accessToken
    refreshToken.value = refresh
    user.value = userInfo
    // 后端 permissions 是字符串数组，直接使用
    permissions.value = userInfo?.permissions || []

    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refresh)
    localStorage.setItem('user', JSON.stringify(userInfo))
  }

  async function register(data: RegisterRequest): Promise<void> {
    await authApi.register(data)
  }

  async function fetchCurrentUser(): Promise<void> {
    const res: any = await authApi.getCurrentUser()
    user.value = res
    permissions.value = res?.permissions || []
    localStorage.setItem('user', JSON.stringify(res))
  }

  async function logout(): Promise<void> {
    // JWT无状态，只需清除客户端存储
    token.value = null
    refreshToken.value = null
    user.value = null
    permissions.value = []
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    router.push('/auth/login')
  }

  function hasPermission(perm: string): boolean {
    return permissions.value.includes(perm)
  }

  function hasRole(roleCode: string): boolean {
    if (!user.value) return false
    // 后端 roles 是字符串数组
    return (user.value.roles || []).includes(roleCode)
  }

  return {
    user, token, refreshToken, permissions, isAuthenticated,
    restoreSession, login, register, fetchCurrentUser, logout, hasPermission, hasRole,
  }
})

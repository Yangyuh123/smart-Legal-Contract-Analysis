import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import type { LoginRequest, RegisterRequest } from '@/types/user'

/**
 * 认证相关组合式函数
 *
 * 在 Pinia auth store 之上提供一层薄封装，统一处理错误反馈与路由跳转，
 * 避免在每个页面组件中重复编写 try/catch + ElMessage.error 样板代码。
 */
export function useAuth() {
  const store = useAuthStore()
  const router = useRouter()

  // ---- 派生状态 ----

  const isAuthenticated = computed(() => store.isAuthenticated)

  const currentUser = computed(() => store.user)

  // ---- 方法 ----

  /** 登录 */
  async function login(credentials: LoginRequest): Promise<boolean> {
    try {
      await store.login(credentials)
      ElMessage.success('登录成功')
      router.push('/dashboard')
      return true
    } catch (err: any) {
      const msg = err?.response?.data?.message || err?.message || '登录失败，请检查账号密码'
      ElMessage.error(msg)
      return false
    }
  }

  /** 注册 */
  async function register(data: RegisterRequest): Promise<boolean> {
    try {
      await store.register(data)
      ElMessage.success('注册成功，请登录')
      router.push('/auth/login')
      return true
    } catch (err: any) {
      const msg = err?.response?.data?.message || err?.message || '注册失败，请稍后重试'
      ElMessage.error(msg)
      return false
    }
  }

  /** 登出 */
  async function logout(): Promise<void> {
    try {
      await store.logout()
      ElMessage.success('已退出登录')
    } catch {
      // store.logout 内部已处理清理，忽略二次错误
    }
  }

  /** 检查当前用户是否拥有指定权限码 */
  function hasPermission(perm: string): boolean {
    return store.hasPermission(perm)
  }

  /** 检查当前用户是否拥有指定角色 */
  function hasRole(roleCode: string): boolean {
    return store.hasRole(roleCode)
  }

  // ---- expose ----
  return {
    isAuthenticated,
    currentUser,
    login,
    register,
    logout,
    hasPermission,
    hasRole,
  }
}

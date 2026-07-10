import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

/**
 * 权限判断组合式函数
 *
 * 提供细粒度的权限与角色判断方法，适用于：
 * - 模板中的 v-if / v-show 条件渲染（按钮/菜单/区块的显隐）
 * - 路由守卫中的辅助判断
 * - 任意需要校验权限的脚本逻辑
 *
 * 所有判断均基于 Pinia authStore 中持有的 permissions[] 与 user.roles[]，
 * 因此必须在应用已初始化 auth store（调用过 restoreSession 或登录后）的情况下使用。
 */
export function usePermission() {
  const authStore = useAuthStore()

  // ---- 权限判断 ----

  /** 是否拥有指定权限码 */
  function hasPermission(perm: string): boolean {
    return authStore.hasPermission(perm)
  }

  /** 是否拥有指定权限列表中的任意一个 */
  function hasAnyPermission(perms: string[]): boolean {
    return perms.some((p) => authStore.hasPermission(p))
  }

  /** 是否拥有指定权限列表中的全部 */
  function hasAllPermissions(perms: string[]): boolean {
    return perms.every((p) => authStore.hasPermission(p))
  }

  // ---- 角色判断 ----

  /** 是否拥有指定角色编码 */
  function hasRole(roleCode: string): boolean {
    return authStore.hasRole(roleCode)
  }

  /** 是否为管理员（角色编码为 "admin"） */
  const isAdmin = computed(() => authStore.hasRole('admin'))

  // ---- 辅助 ----

  /** 用户拥有的全部权限码列表（只读） */
  const permissions = computed(() => authStore.permissions)

  // ---- expose ----
  return {
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    hasRole,
    isAdmin,
    permissions,
  }
}

import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface BreadcrumbItem {
  title: string
  path?: string
}

export const useAppStore = defineStore('app', () => {
  // ---- state ----
  const sidebarCollapsed = ref(false)
  const loading = ref(false)
  const breadcrumbs = ref<BreadcrumbItem[]>([])
  const theme = ref<'light'>('light')
  const locale = ref<'zh-CN'>('zh-CN')

  // ---- actions ----

  /** 切换侧边栏折叠状态 */
  function toggleSidebar(): void {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  /** 设置全局加载状态 */
  function setLoading(val: boolean): void {
    loading.value = val
  }

  /** 设置面包屑导航 */
  function setBreadcrumbs(items: BreadcrumbItem[]): void {
    breadcrumbs.value = items
  }

  // ---- expose ----
  return {
    // state
    sidebarCollapsed,
    loading,
    breadcrumbs,
    theme,
    locale,
    // actions
    toggleSidebar,
    setLoading,
    setBreadcrumbs,
  }
})

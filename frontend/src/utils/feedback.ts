import { createDiscreteApi } from 'naive-ui'
import { themeOverrides } from '@/theme'

/**
 * 离散 API —— 供组件外部(如 axios 拦截器、路由守卫、store)调用反馈。
 *
 * 与 App.vue 内的 n-config-provider 共享同一套 themeOverrides，
 * 保证组件内 useMessage / useDialog 与此处风格完全一致。
 *
 * 用法：
 *   import { message, dialog, notification, loadingBar } from '@/utils/feedback'
 *   message.success('操作成功')
 */
const { message, dialog, notification, loadingBar } = createDiscreteApi(
  ['message', 'dialog', 'notification', 'loadingBar'],
  {
    configProviderProps: {
      themeOverrides,
    },
  },
)

export { message, dialog, notification, loadingBar }

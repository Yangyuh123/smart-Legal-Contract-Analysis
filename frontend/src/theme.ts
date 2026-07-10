import type { GlobalThemeOverrides } from 'naive-ui'

/**
 * 全局主题覆盖 —— 现代 Indigo 设计风格
 *
 * 统一由 App.vue 的 n-config-provider 与 utils/feedback.ts 的
 * createDiscreteApi 共享，保证组件内外反馈风格一致。
 */
export const themeOverrides: GlobalThemeOverrides = {
  common: {
    // 主色 —— Indigo
    primaryColor: '#6366f1',
    primaryColorHover: '#818cf8',
    primaryColorPressed: '#4f46e5',
    primaryColorSuppl: '#818cf8',
    // 语义色
    infoColor: '#3b82f6',
    infoColorHover: '#60a5fa',
    infoColorPressed: '#2563eb',
    successColor: '#10b981',
    successColorHover: '#34d399',
    successColorPressed: '#059669',
    warningColor: '#f59e0b',
    warningColorHover: '#fbbf24',
    warningColorPressed: '#d97706',
    errorColor: '#ef4444',
    errorColorHover: '#f87171',
    errorColorPressed: '#dc2626',
    // 圆角
    borderRadius: '10px',
    borderRadiusSmall: '8px',
    // 字体
    fontSize: '14px',
    fontWeightStrong: '600',
  },
  Card: {
    borderRadius: '14px',
  },
  Button: {
    borderRadiusMedium: '10px',
    fontWeightStrong: '600',
  },
  Menu: {
    borderRadius: '10px',
    itemHeight: '44px',
  },
  Tag: {
    borderRadius: '8px',
  },
  Input: {
    borderRadius: '10px',
  },
  DataTable: {
    borderRadius: '12px',
  },
}

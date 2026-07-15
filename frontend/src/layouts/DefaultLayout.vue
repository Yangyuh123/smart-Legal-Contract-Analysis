<template>
  <n-layout has-sider class="app-shell">
    <n-layout-sider
      bordered
      collapse-mode="width"
      :collapsed-width="64"
      :width="220"
      :collapsed="collapsed"
      show-trigger
      @collapse="collapsed = true"
      @expand="collapsed = false"
      class="app-sider"
    >
      <div class="logo" :class="{ 'logo-collapsed': collapsed }">
        <n-icon :size="26" color="#6366f1"><ShieldCheckmarkOutline /></n-icon>
        <span v-if="!collapsed" class="logo-text">SmartLegal</span>
      </div>
      <n-menu
        :value="activeMenu"
        :options="menuOptions"
        :collapsed="collapsed"
        :collapsed-width="64"
        :indent="20"
        @update:value="handleMenuSelect"
      />
    </n-layout-sider>

    <n-layout>
      <n-layout-header bordered class="app-header">
        <div class="header-title">{{ currentTitle }}</div>
        <div class="header-right">
          <n-badge :value="unreadCount" :max="99" :show="unreadCount > 0">
            <n-button quaternary circle @click="router.push('/notifications')">
              <template #icon>
                <n-icon :size="20"><NotificationsOutline /></n-icon>
              </template>
            </n-button>
          </n-badge>

          <n-dropdown trigger="click" :options="userOptions" @select="handleUserSelect">
            <div class="user-area">
              <n-avatar round :size="32" color="#6366f1">
                {{ (user?.realName || user?.username || 'U').charAt(0).toUpperCase() }}
              </n-avatar>
              <span class="user-name">{{ user?.realName || user?.username || '用户' }}</span>
              <n-icon :size="16"><ChevronDownOutline /></n-icon>
            </div>
          </n-dropdown>
        </div>
      </n-layout-header>

      <n-layout-content class="app-content" content-style="padding: 24px;">
        <router-view v-slot="{ Component }">
          <transition name="fade-slide" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<script setup lang="ts">
import { computed, h, ref, type Component } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NIcon, useDialog } from 'naive-ui'
import type { MenuOption } from 'naive-ui'
import {
  SpeedometerOutline,
  ShieldCheckmarkOutline,
  TimeOutline,
  CreateOutline,
  GitCompareOutline,
  LibraryOutline,
  ChatbubbleEllipsesOutline,
  NotificationsOutline,
  ChevronDownOutline,
  LogOutOutline,
  PersonCircleOutline,
} from '@vicons/ionicons5'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'

const route = useRoute()
const router = useRouter()
const dialog = useDialog()
const auth = useAuthStore()
const notify = useNotificationStore()

const collapsed = ref(false)
const user = computed(() => auth.user)
const unreadCount = computed(() => notify.unreadCount)
const activeMenu = computed(() => route.path)
const currentTitle = computed(() => (route.meta?.title as string) || 'SmartLegal')

function renderIcon(icon: Component) {
  return () => h(NIcon, null, { default: () => h(icon) })
}

const menuOptions: MenuOption[] = [
  { label: '工作台', key: '/dashboard', icon: renderIcon(SpeedometerOutline) },
  { label: '智能审查', key: '/review/create', icon: renderIcon(ShieldCheckmarkOutline) },
  { label: '审查历史', key: '/review/history', icon: renderIcon(TimeOutline) },
  { label: '合同生成', key: '/generate', icon: renderIcon(CreateOutline) },
  { label: '合同比对', key: '/compare', icon: renderIcon(GitCompareOutline) },
  { label: '合规检查', key: '/compliance/create', icon: renderIcon(ShieldCheckmarkOutline) },
  { label: '检查历史', key: '/compliance/history', icon: renderIcon(TimeOutline) },
  {
    label: '知识库',
    key: '/knowledge-group',
    icon: renderIcon(LibraryOutline),
    children: [
      { label: '文档管理', key: '/knowledge' },
      { label: '智能问答', key: '/knowledge/qa' },
    ],
  },
  { label: '消息通知', key: '/notifications', icon: renderIcon(NotificationsOutline) },
]

const userOptions = [
  { label: '个人信息', key: 'profile', icon: renderIcon(PersonCircleOutline) },
  { label: '退出登录', key: 'logout', icon: renderIcon(LogOutOutline) },
]

function handleMenuSelect(key: string) {
  if (key.startsWith('/knowledge-group')) return
  router.push(key)
}

function handleUserSelect(key: string) {
  if (key === 'logout') {
    dialog.warning({
      title: '退出登录',
      content: '确定要退出登录吗？',
      positiveText: '确定',
      negativeText: '取消',
      onPositiveClick: () => auth.logout(),
    })
  }
}
</script>

<style scoped>
.app-shell {
  height: 100vh;
}
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 20px;
  border-bottom: 1px solid var(--sl-border);
}
.logo-collapsed {
  justify-content: center;
  padding: 0;
}
.logo-text {
  font-size: 19px;
  font-weight: 700;
  color: var(--sl-text-1);
  white-space: nowrap;
}
.app-header {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: #fff;
}
.header-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--sl-text-1);
}
.header-right {
  display: flex;
  align-items: center;
  gap: 18px;
}
.user-area {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 10px;
  border-radius: 10px;
  transition: background 0.2s;
}
.user-area:hover {
  background: var(--sl-bg-soft);
}
.user-name {
  font-size: 14px;
  color: var(--sl-text-1);
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.app-content {
  height: calc(100vh - 60px);
  overflow-y: auto;
  background: var(--sl-bg-body);
}
</style>
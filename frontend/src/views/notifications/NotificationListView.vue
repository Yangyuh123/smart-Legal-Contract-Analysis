<template>
  <div class="notification-page sl-page">
    <div class="sl-flex-between" style="margin-bottom: 20px;">
      <div>
        <div class="sl-page-title">通知中心</div>
        <div class="sl-page-subtitle">
          系统消息与审查结果通知
          <n-tag v-if="unreadCount > 0" type="error" size="small" round style="margin-left: 8px;">
            {{ unreadCount }} 条未读
          </n-tag>
        </div>
      </div>
      <n-button v-if="unreadCount > 0" type="primary" secondary :loading="markingAll" @click="handleMarkAllRead">
        <template #icon><n-icon :component="CheckmarkDoneOutline" /></template>
        全部已读
      </n-button>
    </div>

    <n-card :bordered="false">
      <n-spin :show="loading">
        <n-empty v-if="!loading && notifications.length === 0" description="暂无通知" style="padding: 60px 0;" />
        <template v-else>
          <div
            v-for="item in notifications"
            :key="item.id"
            class="n-item"
            :class="{ 'n-unread': item.isRead === 0 }"
            @click="handleClick(item)"
          >
            <div class="n-icon" :style="{ background: iconBg(item.type) }">
              <n-icon :size="18" :color="iconColor(item.type)">
                <component :is="iconComp(item.type)" />
              </n-icon>
            </div>
            <div class="n-body">
              <div class="n-head">
                <span class="n-title">{{ item.title }}</span>
                <span class="n-time">{{ formatTime(item.createTime) }}</span>
              </div>
              <p class="n-content">{{ item.content }}</p>
              <n-tag :type="tagType(item.type)" size="small" round>
                {{ typeLabel(item.type) }}
              </n-tag>
            </div>
            <div class="n-dot" v-if="item.isRead === 0">
              <span class="dot"></span>
            </div>
          </div>
          <div class="pagination" v-if="total > size">
            <n-pagination v-model:page="page" :page-size="size" :item-count="total" @update:page="load" />
          </div>
        </template>
      </n-spin>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, type Component } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import {
  CheckmarkDoneOutline, DocumentOutline, WarningOutline, TimeOutline,
  SettingsOutline, ChatbubbleEllipsesOutline, CheckmarkCircleOutline, NotificationsOutline,
} from '@vicons/ionicons5'
import { notificationApi, type Notification } from '@/api/notification'
import { useNotificationStore } from '@/stores/notification'

const router = useRouter()
const message = useMessage()
const store = useNotificationStore()

const loading = ref(false)
const markingAll = ref(false)
const notifications = ref<Notification[]>([])
const page = ref(1)
const size = ref(15)
const total = ref(0)
const unreadCount = computed(() => store.unreadCount)

let pollTimer: ReturnType<typeof setInterval> | null = null

const labelMap: Record<string, string> = {
  review: '合同审查', compliance: '合规提醒', system: '系统通知',
  generation: '生成完成', comparison: '比对完成',
}
const tagMap: Record<string, '' | 'success' | 'warning' | 'error' | 'info'> = {
  review: 'info', compliance: 'warning', system: 'default', generation: 'success', comparison: 'success',
}
const bgMap: Record<string, string> = {
  review: '#eef2ff', compliance: '#fef0f0', system: '#f4f4f5', generation: '#f0f9eb', comparison: '#f0f9eb',
}
const colorMap: Record<string, string> = {
  review: '#6366f1', compliance: '#ef4444', system: '#909399', generation: '#10b981', comparison: '#10b981',
}
const iconMap: Record<string, Component> = {
  review: DocumentOutline, compliance: WarningOutline, system: SettingsOutline,
  generation: ChatbubbleEllipsesOutline, comparison: CheckmarkCircleOutline,
}

function typeLabel(t: string) { return labelMap[t] || t || '通知' }
function tagType(t: string) { return tagMap[t] || 'info' }
function iconBg(t: string) { return bgMap[t] || '#f4f4f5' }
function iconColor(t: string) { return colorMap[t] || '#909399' }
function iconComp(t: string) { return iconMap[t] || NotificationsOutline }

function formatTime(s: string) {
  if (!s) return '-'
  const d = new Date(s), now = new Date()
  const diff = now.getTime() - d.getTime()
  const min = Math.floor(diff / 60000), hr = Math.floor(diff / 3600000), day = Math.floor(diff / 86400000)
  if (min < 1) return '刚刚'
  if (min < 60) return `${min} 分钟前`
  if (hr < 24) return `${hr} 小时前`
  if (day < 7) return `${day} 天前`
  return d.toLocaleDateString('zh-CN')
}

async function load() {
  loading.value = true
  try {
    const res = await notificationApi.list({ page: page.value, size: size.value })
    notifications.value = res.records
    total.value = res.total
  } catch {
    notifications.value = []
  } finally {
    loading.value = false
  }
}

async function handleClick(item: Notification) {
  if (item.isRead === 0) {
    try {
      await notificationApi.markRead(item.id)
      item.isRead = 1
      store.decrementUnread()
    } catch { /* ignore */ }
  }
  if (item.relatedId) {
    const map: Record<string, string> = {
      review: `/review/${item.relatedId}`, comparison: `/compare/${item.relatedId}`,
    }
    const path = map[item.type]
    if (path) router.push(path)
  }
}

async function handleMarkAllRead() {
  markingAll.value = true
  try {
    await notificationApi.markAllRead()
    notifications.value.forEach(n => { n.isRead = 1 })
    store.markAllAsRead()
    message.success('已全部标为已读')
  } catch {
    message.error('操作失败')
  } finally {
    markingAll.value = false
  }
}

onMounted(async () => {
  await store.fetchUnreadCount()
  await load()
  pollTimer = setInterval(() => store.fetchUnreadCount(), 30000)
})

onBeforeUnmount(() => {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
})
</script>

<style scoped>
.n-item {
  display: flex; gap: 14px; padding: 14px 16px;
  border-bottom: 1px solid var(--sl-border); cursor: pointer; transition: background 0.2s;
}
.n-item:hover { background: #f9fafb; }
.n-unread { background: #f0f7ff; }
.n-unread:hover { background: #e6f0fc; }
.n-item:last-child { border-bottom: none; }
.n-icon {
  width: 38px; height: 38px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.n-body { flex: 1; min-width: 0; }
.n-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 4px; }
.n-title { font-size: 14px; font-weight: 600; color: var(--sl-text-1); flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.n-time { font-size: 12px; color: var(--sl-text-3); flex-shrink: 0; margin-left: 12px; }
.n-content { font-size: 13px; color: var(--sl-text-2); line-height: 1.5; margin: 0 0 6px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.n-dot { display: flex; align-items: center; flex-shrink: 0; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: #6366f1; }
.pagination { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>

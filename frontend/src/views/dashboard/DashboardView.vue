<template>
  <div class="dashboard sl-page">
    <div class="sl-page-title">工作台</div>
    <div class="sl-page-subtitle">合同审查数据总览</div>

    <n-spin :show="loading">
      <!-- 统计卡片 -->
      <n-grid :x-gap="16" :y-gap="16" :cols="4" item-responsive responsive="screen">
        <n-gi v-for="s in stats" :key="s.label" span="4 s:2 l:1">
          <n-card class="stat-card" :bordered="false">
            <div class="stat-content">
              <div class="stat-icon" :style="{ background: s.bg }">
                <n-icon :size="26" color="#fff"><component :is="s.icon" /></n-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ s.value }}</div>
                <div class="stat-label">{{ s.label }}</div>
              </div>
            </div>
          </n-card>
        </n-gi>
      </n-grid>

      <!-- 中部区域 -->
      <n-grid :x-gap="16" :y-gap="16" :cols="2" item-responsive responsive="screen" style="margin-top: 16px;">
        <n-gi span="2 l:1">
          <n-card title="审查统计（近1个月）" :bordered="false">
            <div style="height: 300px;">
              <v-chart v-if="!chartLoading" :option="reviewChartOption" autoresize style="width:100%;height:100%" />
              <n-skeleton v-else :repeat="6" text />
            </div>
          </n-card>
        </n-gi>
        <n-gi span="2 l:1">
          <n-card title="最近审查" :bordered="false">
            <n-empty v-if="recentReviews.length === 0 && !chartLoading" description="暂无审查记录" style="padding: 48px 0;">
              <template #extra>
                <n-button size="small" type="primary" @click="router.push('/review/create')">发起首次审查</n-button>
              </template>
            </n-empty>
            <div v-else>
              <div v-for="r in recentReviews.slice(0, 6)" :key="r.id" class="recent-item">
                <div class="recent-left">
                  <span class="recent-title">{{ r.contractTitle || '合同审查' }}</span>
                  <span class="recent-time">{{ formatRelativeTime(r.createTime) }}</span>
                </div>
                <div class="recent-right">
                  <n-tag :type="r.status === 'COMPLETED' ? 'success' : 'warning'" size="small" round>
                    {{ r.status === 'COMPLETED' ? '已完成' : '处理中' }}
                  </n-tag>
                  <span class="risk-summary">
                    <b style="color:#ef4444">{{ r.criticalRisks || 0 }}</b> /
                    <b style="color:#f59e0b">{{ r.generalRisks || 0 }}</b> /
                    <b style="color:#9ca3af">{{ r.lowRisks || 0 }}</b>
                  </span>
                </div>
              </div>
            </div>
          </n-card>
        </n-gi>
      </n-grid>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, markRaw } from 'vue'
import { useRouter } from 'vue-router'
import { ShieldCheckmarkOutline, CalendarOutline, WarningOutline, CreateOutline } from '@vicons/ionicons5'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, GridComponent } from 'echarts/components'
import { reviewApi } from '@/api/reviews'
import { formatRelativeTime } from '@/utils/format'

use([CanvasRenderer, BarChart, TitleComponent, TooltipComponent, GridComponent])

const router = useRouter()
const loading = ref(false)
const chartLoading = ref(true)
const recentReviews = ref<any[]>([])

const stats = reactive([
  { label: '审查总数', value: 0, icon: markRaw(ShieldCheckmarkOutline), bg: '#6366f1' },
  { label: '本月审查', value: 0, icon: markRaw(CalendarOutline), bg: '#10b981' },
  { label: '风险预警', value: 0, icon: markRaw(WarningOutline), bg: '#ef4444' },
  { label: '今日操作', value: 0, icon: markRaw(CreateOutline), bg: '#8b5cf6' },
])

const chartData = reactive({ days: [] as string[], counts: [] as number[] })

const reviewChartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: {
    type: 'category',
    data: chartData.days,
    axisLabel: { rotate: 45, fontSize: 10, interval: 1 },
    boundaryGap: true,
  },
  yAxis: { type: 'value', name: '审查次数', minInterval: 1 },
  series: [{
    type: 'bar',
    data: chartData.counts,
    itemStyle: { color: '#6366f1', borderRadius: [4, 4, 0, 0] },
    barWidth: '60%',
  }],
}))

onMounted(async () => {
  loading.value = true
  try {
    const res = await reviewApi.list({ page: 1, size: 100 })
    const all = res.records || []
    recentReviews.value = all
    stats[0].value = all.length

    const now = new Date()
    stats[1].value = all.filter((r: any) => new Date(r.createTime).getMonth() === now.getMonth()).length

    let high = 0
    all.forEach((r: any) => { if (r.criticalRisks) high += r.criticalRisks })
    stats[2].value = high
    stats[3].value = all.filter((r: any) => new Date(r.createTime).toDateString() === now.toDateString()).length

    const days: string[] = [], counts: number[] = []
    for (let i = 29; i >= 0; i--) {
      const d = new Date(now.getFullYear(), now.getMonth(), now.getDate() - i)
      const label = `${d.getMonth() + 1}/${d.getDate()}`
      days.push(label)
      counts.push(all.filter((r: any) => {
        const rd = new Date(r.createTime)
        return rd.toDateString() === d.toDateString()
      }).length)
    }
    chartData.days = days
    chartData.counts = counts
  } catch { /* use defaults */ }
  finally { loading.value = false; chartLoading.value = false }
})
</script>

<style scoped>
.stat-card :deep(.n-card__content) {
  padding: 20px;
}
.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}
.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--sl-text-1);
  line-height: 1.2;
}
.stat-label {
  font-size: 14px;
  color: var(--sl-text-3);
}
.recent-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--sl-border);
}
.recent-item:last-child {
  border-bottom: none;
}
.recent-title {
  display: block;
  font-size: 14px;
  color: var(--sl-text-1);
}
.recent-time {
  font-size: 12px;
  color: var(--sl-text-3);
}
.recent-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.risk-summary {
  font-size: 13px;
  color: var(--sl-text-2);
}
</style>

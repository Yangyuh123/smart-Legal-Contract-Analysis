<template>
  <div class="history-page sl-page">
    <div class="sl-page-title">审查历史</div>
    <div class="sl-page-subtitle">查看历史合同审查记录</div>

    <n-card :bordered="false">
      <n-spin :show="loading">
        <n-data-table
          :columns="columns"
          :data="list"
          :bordered="false"
          :row-key="(row: any) => row.id"
        />
        <div class="pagination" v-if="total > size">
          <n-pagination
            v-model:page="page"
            :page-size="size"
            :item-count="total"
            @update:page="load"
          />
        </div>
      </n-spin>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, h, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NTag, type DataTableColumns } from 'naive-ui'
import { reviewApi, type ReviewRecord } from '@/api/reviews'

const router = useRouter()
const loading = ref(false)
const list = ref<ReviewRecord[]>([])
const page = ref(1)
const size = ref(10)
const total = ref(0)

const statusMap: Record<string, { type: any; text: string }> = {
  COMPLETED: { type: 'success', text: '已完成' },
  PROCESSING: { type: 'warning', text: '审查中' },
  FAILED: { type: 'error', text: '失败' },
}

const columns: DataTableColumns<ReviewRecord> = [
  {
    title: '文件名',
    key: 'fileName',
    minWidth: 200,
    ellipsis: { tooltip: true },
    render: (row) => row.fileName || row.contractTitle || '-',
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render: (row) => {
      const s = statusMap[row.status] || { type: 'default', text: '待处理' }
      return h(NTag, { type: s.type, size: 'small', round: true }, { default: () => s.text })
    },
  },
  {
    title: '风险',
    key: 'risks',
    width: 220,
    render: (row) => {
      if (!row.totalRisks) return '-'
      const items = []
      if (row.criticalRisks) items.push(h('span', { class: 'rc critical' }, `重大 ${row.criticalRisks}`))
      if (row.generalRisks) items.push(h('span', { class: 'rc general' }, `一般 ${row.generalRisks}`))
      if (row.lowRisks) items.push(h('span', { class: 'rc low' }, `低 ${row.lowRisks}`))
      return h('div', {}, items)
    },
  },
  {
    title: '审查时间',
    key: 'createTime',
    width: 170,
    render: (row) => row.createTime?.substring(0, 16) || '-',
  },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    render: (row) =>
      row.status === 'COMPLETED'
        ? h(NButton, { text: true, type: 'primary', size: 'small', onClick: () => router.push(`/review/${row.id}`) }, { default: () => '查看详情' })
        : h('span', { style: 'color: var(--sl-text-3)' }, '处理中'),
  },
]

async function load() {
  loading.value = true
  try {
    const res = await reviewApi.list({ page: page.value, size: size.value })
    list.value = res.records || []
    total.value = res.total || 0
  } catch {
    list.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

onMounted(() => load())
</script>

<style scoped>
.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
:deep(.rc) {
  margin-right: 8px;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 6px;
}
:deep(.rc.critical) {
  background: #fef2f2;
  color: #ef4444;
}
:deep(.rc.general) {
  background: #fffbeb;
  color: #f59e0b;
}
:deep(.rc.low) {
  background: #f9fafb;
  color: #6b7280;
}
</style>

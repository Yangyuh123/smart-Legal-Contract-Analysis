<template>
  <div class="compliance-history-page sl-page">
    <div class="sl-page-title">合规检查历史</div>

    <n-button type="primary" @click="router.push('/compliance/create')" style="margin-bottom: 16px;">
      <template #icon><n-icon :component="PlusOutline" /></template>
      新建检查
    </n-button>

    <n-card :bordered="false">
      <n-table
        :columns="columns"
        :data="records"
        :pagination="pagination"
        :loading="loading"
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
      />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { PlusOutline } from '@vicons/ionicons5'
import { complianceApi, type ComplianceRecord } from '@/api/compliance'

const router = useRouter()
const loading = ref(false)
const records = ref<ComplianceRecord[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)

const pagination = computed(() => ({
  page: page.value,
  pageSize: pageSize.value,
  itemCount: total.value,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  showQuickJumper: true,
}))

const columns = [
  {
    title: '文件名称',
    key: 'fileName',
    render(row: ComplianceRecord) {
      return {
        type: 'button',
        text: row.fileName,
        onClick: () => router.push(`/compliance/${row.id}`),
      }
    },
  },
  {
    title: '合规标准',
    key: 'complianceStandard',
  },
  {
    title: '合规状态',
    key: 'overallCompliance',
    render(row: ComplianceRecord) {
      const status = row.overallCompliance
      const type = status === 'compliant' ? 'success' : status === 'partially_compliant' ? 'warning' : 'error'
      const label = status === 'compliant' ? '符合要求' : status === 'partially_compliant' ? '部分符合' : '不符合'
      return {
        type: 'tag',
        text: label,
        type: type as 'success' | 'warning' | 'error',
      }
    },
  },
  {
    title: '问题总数',
    key: 'totalIssues',
    render(row: ComplianceRecord) {
      const count = row.totalIssues || 0
      return count > 0 ? { type: 'tag', text: count, type: 'error' as const } : count
    },
  },
  {
    title: '创建时间',
    key: 'createTime',
    render(row: ComplianceRecord) {
      return new Date(row.createTime).toLocaleString('zh-CN')
    },
  },
]

async function loadData() {
  loading.value = true
  try {
    const data = await complianceApi.list({ page: page.value, size: pageSize.value })
    records.value = data.records || []
    total.value = data.total || 0
  } finally {
    loading.value = false
  }
}

function handlePageChange(pageNum: number) {
  page.value = pageNum
  loadData()
}

function handlePageSizeChange(size: number) {
  pageSize.value = size
  page.value = 1
  loadData()
}

loadData()
</script>

<style scoped>
</style>
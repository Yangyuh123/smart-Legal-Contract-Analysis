<template>
  <div class="cmp-result sl-page">
    <div class="sl-flex-between" style="margin-bottom: 16px;">
      <div class="sl-page-title">比对结果</div>
      <n-button @click="router.push('/compare')">
        <template #icon><n-icon :component="ArrowBackOutline" /></template>
        返回
      </n-button>
    </div>

    <n-spin :show="loading">
      <template v-if="result">
        <!-- 统计 -->
        <n-grid :cols="4" :x-gap="16" item-responsive responsive="screen">
          <n-gi span="2 s:1">
            <div class="stat-box" style="background:#ecfdf5">
              <div class="stat-num" style="color:#059669">{{ result.similarity || 0 }}%</div>
              <div class="stat-label">相似度</div>
            </div>
          </n-gi>
          <n-gi span="2 s:1">
            <div class="stat-box" style="background:#ecfdf5">
              <div class="stat-num" style="color:#059669">{{ additions }}</div>
              <div class="stat-label">新增</div>
            </div>
          </n-gi>
          <n-gi span="2 s:1">
            <div class="stat-box" style="background:#fef2f2">
              <div class="stat-num" style="color:#ef4444">{{ deletions }}</div>
              <div class="stat-label">删除</div>
            </div>
          </n-gi>
          <n-gi span="2 s:1">
            <div class="stat-box" style="background:#fffbeb">
              <div class="stat-num" style="color:#f59e0b">{{ modifications }}</div>
              <div class="stat-label">修改</div>
            </div>
          </n-gi>
        </n-grid>

        <!-- 差异明细 -->
        <n-card :bordered="false" style="margin-top: 16px;" :title="`差异明细（${diffs.length}项）`">
          <n-empty v-if="diffs.length === 0" description="未发现差异" />
          <div v-for="(d, i) in diffs" :key="i" class="diff-item">
            <div class="diff-head">
              <n-tag
                :type="d.diffType === 'addition' ? 'success' : d.diffType === 'deletion' ? 'error' : 'warning'"
                size="small"
              >
                {{ d.diffType === 'addition' ? '新增' : d.diffType === 'deletion' ? '删除' : '修改' }}
              </n-tag>
              <span v-if="d.clauseSection" class="diff-clause">{{ d.clauseSection }}</span>
            </div>
            <div class="diff-body" v-if="d.contentA || d.contentB">
              <div class="diff-side old" v-if="d.contentA">
                <div class="diff-label">合同A</div>
                <div class="diff-text">{{ d.contentA }}</div>
              </div>
              <div class="diff-side new" v-if="d.contentB">
                <div class="diff-label">合同B</div>
                <div class="diff-text">{{ d.contentB }}</div>
              </div>
            </div>
            <div v-if="d.summary" class="diff-summary">{{ d.summary }}</div>
          </div>
        </n-card>
      </template>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowBackOutline } from '@vicons/ionicons5'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const result = ref<any>(null)
const diffs = ref<any[]>([])
const additions = ref(0)
const deletions = ref(0)
const modifications = ref(0)

onMounted(async () => {
  const id = route.params.id as string
  if (!id) return
  loading.value = true
  try {
    const token = localStorage.getItem('access_token')
    const resp = await fetch(`/api/v1/comparisons/${id}`, { headers: { Authorization: `Bearer ${token}` } })
    const data = await resp.json()
    if (data.code === 200) {
      result.value = data.data
      diffs.value = data.data.diffs || []
      additions.value = diffs.value.filter((d: any) => d.diffType === 'addition').length
      deletions.value = diffs.value.filter((d: any) => d.diffType === 'deletion').length
      modifications.value = diffs.value.filter((d: any) => d.diffType === 'modification').length
    }
  } catch { /* ignore */ }
  finally { loading.value = false }
})
</script>

<style scoped>
.stat-box {
  text-align: center;
  padding: 18px;
  border-radius: 12px;
}
.stat-num {
  font-size: 28px;
  font-weight: 700;
}
.stat-label {
  font-size: 13px;
  color: var(--sl-text-2);
  margin-top: 4px;
}
.diff-item {
  padding: 12px;
  border: 1px solid var(--sl-border);
  border-radius: 10px;
  margin-bottom: 10px;
}
.diff-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.diff-clause {
  font-weight: 600;
  font-size: 14px;
  color: var(--sl-text-1);
}
.diff-body {
  display: flex;
  gap: 12px;
}
.diff-side {
  flex: 1;
}
.diff-label {
  font-size: 12px;
  color: var(--sl-text-3);
  margin-bottom: 4px;
}
.diff-text {
  padding: 8px 10px;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.6;
}
.diff-side.old .diff-text {
  background: #fef2f2;
  color: #ef4444;
  text-decoration: line-through;
}
.diff-side.new .diff-text {
  background: #ecfdf5;
  color: #059669;
}
.diff-summary {
  font-size: 13px;
  color: var(--sl-text-3);
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--sl-border);
}
</style>

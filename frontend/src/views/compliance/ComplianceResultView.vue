<template>
  <div class="compliance-result-page sl-page">
    <div class="sl-page-title">合规检查结果</div>

    <!-- 返回按钮 -->
    <n-button text @click="router.push('/compliance/create')" style="margin-bottom: 16px;">
      <template #icon><n-icon :component="ArrowBackOutline" /></template>
      返回检查
    </n-button>

    <!-- 加载状态 -->
    <n-spin v-if="loading" />

    <!-- 结果内容 -->
    <div v-else-if="record">
      <!-- 文件信息卡片 -->
      <n-card :bordered="false" style="margin-bottom: 16px;">
        <div class="result-header">
          <n-icon :size="48" color="#6366f1"><DocumentTextOutline /></n-icon>
          <div class="result-info">
            <h3>{{ record.fileName }}</h3>
            <p class="result-meta">
              <span class="meta-item">合规标准：{{ record.complianceStandard }}</span>
              <span class="meta-item">行业：{{ record.industry }}</span>
              <span class="meta-item">地区：{{ record.jurisdiction }}</span>
            </p>
          </div>
          <n-tag :type="complianceType" round>
            {{ complianceLabel }}
          </n-tag>
        </div>
      </n-card>

      <!-- 统计卡片 -->
      <n-card :bordered="false" style="margin-bottom: 16px;">
        <div class="stats-grid">
          <div class="stat-item">
            <n-icon :size="28" color="#ef4444"><AlertTriangleOutline /></n-icon>
            <div class="stat-content">
              <strong>{{ record.criticalIssues || 0 }}</strong>
              <span>严重问题</span>
            </div>
          </div>
          <div class="stat-item">
            <n-icon :size="28" color="#f59e0b"><AlertCircleOutline /></n-icon>
            <div class="stat-content">
              <strong>{{ record.generalIssues || 0 }}</strong>
              <span>一般问题</span>
            </div>
          </div>
          <div class="stat-item">
            <n-icon :size="28" color="#3b82f6"><InfoOutline /></n-icon>
            <div class="stat-content">
              <strong>{{ record.lowIssues || 0 }}</strong>
              <span>轻微问题</span>
            </div>
          </div>
          <div class="stat-item">
            <n-icon :size="28" color="#10b981"><CheckCircle2Outline /></n-icon>
            <div class="stat-content">
              <strong>{{ record.totalIssues || 0 }}</strong>
              <span>问题总数</span>
            </div>
          </div>
        </div>
      </n-card>

      <!-- 检查摘要 -->
      <n-card :bordered="false" style="margin-bottom: 16px;">
        <template #header>
          <span class="card-header">检查摘要</span>
        </template>
        <p>{{ record.summary || '暂无摘要' }}</p>
      </n-card>

      <!-- 问题列表 -->
      <n-card :bordered="false">
        <template #header>
          <span class="card-header">问题详情</span>
        </template>
        <n-empty v-if="!record.issues || record.issues.length === 0" description="未发现合规问题" />
        <div v-else class="issues-list">
          <n-collapse :default-expanded-names="record.issues.map((_, i) => String(i))">
            <n-collapse-item
              v-for="(issue, index) in record.issues"
              :key="issue.id"
              :name="String(index)"
            >
              <template #header>
                <div class="issue-header">
                  <n-tag :type="getSeverityType(issue.severity)" size="small">
                    {{ getSeverityLabel(issue.severity) }}
                  </n-tag>
                  <span class="issue-title">{{ issue.issueTitle }}</span>
                  <span v-if="issue.clauseReference" class="issue-clause">{{ issue.clauseReference }}</span>
                </div>
              </template>
              <div class="issue-content">
                <div class="issue-section">
                  <strong>问题描述：</strong>
                  <p>{{ issue.description }}</p>
                </div>
                <div v-if="issue.legalReference" class="issue-section">
                  <strong>法律依据：</strong>
                  <p>{{ issue.legalReference }}</p>
                </div>
                <div v-if="issue.recommendation" class="issue-section">
                  <strong>整改建议：</strong>
                  <p>{{ issue.recommendation }}</p>
                </div>
                <div v-if="issue.penaltyRisk" class="issue-section">
                  <strong>处罚风险：</strong>
                  <p>{{ issue.penaltyRisk }}</p>
                </div>
              </div>
            </n-collapse-item>
          </n-collapse>
        </div>
      </n-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  ArrowBackOutline,
  DocumentTextOutline,
  AlertTriangleOutline,
  AlertCircleOutline,
  InfoOutline,
  CheckCircle2Outline,
} from '@vicons/ionicons5'
import { complianceApi, type ComplianceRecord, type Severity } from '@/api/compliance'

const router = useRouter()
const route = useRoute()
const loading = ref(true)
const record = ref<ComplianceRecord | null>(null)

const complianceType = computed(() => {
  const status = record.value?.overallCompliance
  if (status === 'compliant') return 'success'
  if (status === 'partially_compliant') return 'warning'
  return 'error'
})

const complianceLabel = computed(() => {
  const status = record.value?.overallCompliance
  if (status === 'compliant') return '符合要求'
  if (status === 'partially_compliant') return '部分符合'
  return '不符合'
})

function getSeverityType(severity: Severity): 'error' | 'warning' | 'info' {
  switch (severity) {
    case 'CRITICAL': return 'error'
    case 'GENERAL': return 'warning'
    default: return 'info'
  }
}

function getSeverityLabel(severity: Severity): string {
  switch (severity) {
    case 'CRITICAL': return '严重'
    case 'GENERAL': return '一般'
    default: return '轻微'
  }
}

async function loadData() {
  const id = Number(route.params.id)
  if (!id) return
  loading.value = true
  try {
    record.value = await complianceApi.getById(id)
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.result-header {
  display: flex;
  align-items: center;
  gap: 16px;
}
.result-info h3 {
  margin: 0;
  font-size: 18px;
}
.result-meta {
  margin: 8px 0 0;
  font-size: 13px;
  color: var(--sl-text-3);
}
.meta-item {
  margin-right: 16px;
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.stat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: var(--sl-bg-soft);
  border-radius: 12px;
}
.stat-content strong {
  display: block;
  font-size: 24px;
  font-weight: 700;
}
.stat-content span {
  font-size: 13px;
  color: var(--sl-text-3);
}
.card-header {
  font-weight: 600;
}
.issue-header {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}
.issue-title {
  flex: 1;
  font-weight: 500;
}
.issue-clause {
  font-size: 13px;
  color: var(--sl-text-3);
}
.issue-content {
  padding-top: 12px;
}
.issue-section {
  margin-bottom: 12px;
}
.issue-section:last-child {
  margin-bottom: 0;
}
.issue-section p {
  margin: 4px 0 0;
  font-size: 14px;
  line-height: 1.6;
}
</style>
<template>
  <div class="result-page sl-page">
    <div class="sl-flex-between" style="margin-bottom: 16px;">
      <div class="sl-page-title">审查报告</div>
      <div style="display: flex; gap: 8px;">
        <n-button v-if="acceptedIndices.size > 0" type="success" @click="showExportDialog = true">
          <template #icon><n-icon :component="DownloadOutline" /></template>
          导出修改后合同
        </n-button>
        <n-button @click="router.push('/review/history')">
          <template #icon><n-icon :component="ArrowBackOutline" /></template>
          返回列表
        </n-button>
      </div>
    </div>

    <n-spin :show="loading">
      <template v-if="record">
        <!-- 摘要 -->
        <n-grid :cols="4" :x-gap="16" responsive="screen" item-responsive>
          <n-gi v-for="s in summary" :key="s.label" span="2 s:1">
            <div class="stat-box" :style="{ background: s.bg }">
              <div class="stat-num" :style="{ color: s.color }">{{ s.value }}</div>
              <div class="stat-label">{{ s.label }}</div>
            </div>
          </n-gi>
        </n-grid>

        <!-- 左右布局 - 等高 -->
        <div class="dual-panel" style="margin-top: 16px;">
          <div class="dual-left">
            <n-card :bordered="false" title="合同原文" class="fill-card">
              <template #header-extra>
                <n-tag v-if="acceptedIndices.size > 0" type="success" size="small">
                  已应用 {{ acceptedIndices.size }} 处修改
                </n-tag>
              </template>
              <div class="doc-view" v-if="record.contentText">
                <div
                  v-for="(p, i) in contentParagraphs"
                  :key="i"
                  :class="['doc-para', { 'doc-empty': p.isEmpty, 'accepted': p.accepted }]"
                >
                  <template v-if="!p.isEmpty">
                    <span
                      v-for="(seg, si) in p.segments"
                      :key="si"
                      class="para-text"
                      :style="seg.style"
                    >{{ seg.text }}</span>
                  </template>
                </div>
              </div>
              <n-empty v-else description="暂无文件内容" />
            </n-card>
          </div>
          <div class="dual-right">
            <n-card :bordered="false" class="fill-card">
              <template #header>
                <div class="risk-header">
                  <span>风险清单（{{ risks.length }}项）</span>
                  <n-radio-group v-model:value="filter" size="small">
                    <n-radio-button value="">全部</n-radio-button>
                    <n-radio-button value="CRITICAL">重大</n-radio-button>
                    <n-radio-button value="GENERAL">一般</n-radio-button>
                    <n-radio-button value="LOW">低</n-radio-button>
                  </n-radio-group>
                </div>
              </template>
              <div class="risk-list">
                <div
                  v-for="(r, idx) in filteredRisks"
                  :key="r.id"
                  class="r-item"
                  :class="[
                    'r-' + (r.riskLevel || '').toLowerCase(),
                    { 'r-accepted': isAccepted(idx) },
                  ]"
                >
                  <div class="r-head">
                    <n-tag
                      :type="r.riskLevel === 'CRITICAL' ? 'error' : r.riskLevel === 'GENERAL' ? 'warning' : 'default'"
                      size="small"
                    >
                      {{ r.riskLevel === 'CRITICAL' ? '重大' : r.riskLevel === 'GENERAL' ? '一般' : '低' }}
                    </n-tag>
                    <strong>{{ r.riskTitle }}</strong>
                  </div>
                  <p>{{ r.riskDescription }}</p>
                  <div v-if="r.riskPosition" class="r-quote">"{{ r.riskPosition?.substring(0, 150) }}"</div>
                  <div v-if="r.suggestedText" class="r-fix">
                    <strong>建议修改：</strong>{{ r.suggestedText }}
                  </div>
                  <div v-if="r.legalBasis" class="r-law">依据：{{ r.legalBasis }}</div>
                  <div v-if="r.suggestedText" class="r-action">
                    <n-button
                      v-if="!isAccepted(idx)"
                      type="success"
                      size="small"
                      secondary
                      @click="acceptSuggestion(idx)"
                    >
                      <template #icon><n-icon :component="CheckmarkOutline" /></template>
                      采纳建议
                    </n-button>
                    <n-tag v-else type="success" size="small">
                      <template #icon><n-icon :component="CheckmarkOutline" /></template>
                      已采纳
                    </n-tag>
                  </div>
                </div>
                <n-empty v-if="filteredRisks.length === 0" description="暂无风险项" />
              </div>
            </n-card>
          </div>
        </div>
      </template>
    </n-spin>

    <!-- 导出对话框 -->
    <n-modal v-model:show="showExportDialog" preset="dialog" title="导出修改后的合同" positive-text="导出" @positive-click="handleExport" style="width: 420px;">
      <p style="margin-bottom: 12px;">已应用 <strong>{{ acceptedIndices.size }}</strong> 处修改建议，选择导出格式：</p>
      <n-radio-group v-model:value="exportFormat">
        <n-radio-button value="docx">DOCX</n-radio-button>
        <n-radio-button value="pdf">PDF</n-radio-button>
      </n-radio-group>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import {
  ArrowBackOutline,
  DownloadOutline,
  CheckmarkOutline,
} from '@vicons/ionicons5'
import { reviewApi, type ReviewRecord, type ReviewRisk } from '@/api/reviews'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const loading = ref(false)
const record = ref<(ReviewRecord & { contentText?: string }) | null>(null)
const risks = ref<ReviewRisk[]>([])
const filter = ref('')
const acceptedIndices = ref<Set<number>>(new Set())
const showExportDialog = ref(false)
const exportFormat = ref('docx')

const summary = computed(() => [
  { label: '重大风险', value: record.value?.criticalRisks || 0, color: '#ef4444', bg: '#fef2f2' },
  { label: '一般风险', value: record.value?.generalRisks || 0, color: '#f59e0b', bg: '#fffbeb' },
  { label: '低风险', value: record.value?.lowRisks || 0, color: '#6b7280', bg: '#f9fafb' },
  { label: '风险总计', value: record.value?.totalRisks || 0, color: '#6366f1', bg: '#eef2ff' },
])

const filteredRisks = computed(() =>
  filter.value ? risks.value.filter(r => r.riskLevel === filter.value) : risks.value,
)

/** 带段落标记的内容段落 */
interface TextSegment {
  text: string
  style: Record<string, string>
}
interface ContentParagraph {
  text: string
  segments: TextSegment[]
  accepted: boolean
  isEmpty: boolean
}

/** 风险等级对应的背景色 */
const riskColors: Record<string, string> = {
  CRITICAL: '#fee2e2',
  GENERAL: '#fef9c3',
  LOW: '#ffedd5',
}

/** 将一段文本按风险匹配位置拆分为多个带样式的片段 */
function buildSegments(text: string, isAccepted: boolean): TextSegment[] {
  // 已采纳段落：整段用绿色背景标记
  if (isAccepted) {
    return [{ text, style: { backgroundColor: '#dcfce7', borderRadius: '2px', padding: '0 1px' } }]
  }
  // 未采纳段落：精确匹配风险文字片段，用对应风险等级颜色填充
  const matches: { start: number; end: number; color: string }[] = []
  for (const r of risks.value) {
    if (!r.riskPosition) continue
    const searchText = r.riskPosition.substring(0, 30)
    const idx = text.indexOf(searchText)
    if (idx !== -1) {
      const color = riskColors[r.riskLevel || 'LOW'] || '#ffedd5'
      const newMatch = { start: idx, end: idx + searchText.length, color }
      let merged = false
      for (const m of matches) {
        if (newMatch.start <= m.end && newMatch.end >= m.start) {
          m.start = Math.min(m.start, newMatch.start)
          m.end = Math.max(m.end, newMatch.end)
          merged = true
          break
        }
      }
      if (!merged) matches.push(newMatch)
    }
  }
  if (matches.length === 0) return [{ text, style: {} }]
  matches.sort((a, b) => a.start - b.start)
  const segments: TextSegment[] = []
  let cursor = 0
  for (const m of matches) {
    if (m.start > cursor) {
      segments.push({ text: text.slice(cursor, m.start), style: {} })
    }
    segments.push({
      text: text.slice(m.start, m.end),
      style: { backgroundColor: m.color, borderRadius: '2px', padding: '0 1px' },
    })
    cursor = m.end
  }
  if (cursor < text.length) {
    segments.push({ text: text.slice(cursor), style: {} })
  }
  return segments
}

/** 已采纳的段落索引集合（以段落索引为 key，而非风险索引） */
const acceptedParaIndices = ref<Set<number>>(new Set())

const contentParagraphs = computed<ContentParagraph[]>(() => {
  if (!record.value?.contentText) return []
  // 保留所有行（包括空行），严格还原原合同换行格式
  const allLines = record.value.contentText.split('\n')
  return allLines.map((text, paraIdx) => {
    const isEmpty = !text.trim()
    const accepted = acceptedParaIndices.value.has(paraIdx)
    return {
      text,
      segments: isEmpty ? [] : buildSegments(text, accepted),
      accepted,
      isEmpty,
    }
  })
})

/** 获取 filteredRisks 中的原始索引 */
function getOriginalIndex(filteredIdx: number): number {
  if (!filter.value) return filteredIdx
  let count = 0
  for (let i = 0; i < risks.value.length; i++) {
    if (risks.value[i].riskLevel === filter.value) {
      if (count === filteredIdx) return i
      count++
    }
  }
  return -1
}

function isAccepted(filteredIdx: number): boolean {
  const origIdx = getOriginalIndex(filteredIdx)
  return acceptedIndices.value.has(origIdx)
}

function acceptSuggestion(filteredIdx: number) {
  const origIdx = getOriginalIndex(filteredIdx)
  if (origIdx < 0) return
  const risk = risks.value[origIdx]
  if (!risk?.suggestedText || !record.value?.contentText) return

  // 替换合同原文中的对应内容，并记录被替换的段落索引
  if (risk.riskPosition) {
    const searchText = risk.riskPosition.substring(0, 40)
    const content = record.value.contentText
    const pos = content.indexOf(searchText)
    if (pos !== -1) {
      // 计算被替换文字跨越了哪些段落索引
      const textBefore = content.substring(0, pos)
      const startParaIdx = textBefore.split('\n').length - 1
      const replacedText = content.substring(pos, pos + searchText.length)
      const lineCount = replacedText.split('\n').length
      const newSet = new Set(acceptedParaIndices.value)
      for (let j = startParaIdx; j < startParaIdx + lineCount; j++) {
        newSet.add(j)
      }
      acceptedParaIndices.value = newSet

      record.value.contentText = content.substring(0, pos) + risk.suggestedText + content.substring(pos + searchText.length)
    }
  }
  acceptedIndices.value.add(origIdx)
  acceptedIndices.value = new Set(acceptedIndices.value)
  message.success('已采纳修改建议')
}

/** 导出修改后的合同 */
async function handleExport() {
  if (!record.value) return
  try {
    const token = localStorage.getItem('access_token')
    const resp = await fetch(`/api/v1/reviews/${record.value.id}/export`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        format: exportFormat.value,
        contentText: record.value.contentText,
        fileName: record.value.fileName || 'contract',
      }),
    })
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}))
      throw new Error(err.message || '导出失败')
    }
    const blob = await resp.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    const ext = exportFormat.value
    const baseName = (record.value.fileName || 'contract').replace(/\.[^.]+$/, '')
    a.href = url
    a.download = `${baseName}_modified.${ext}`
    a.click()
    URL.revokeObjectURL(url)
    message.success('导出成功')
  } catch (e: any) {
    message.error(e.message || '导出失败')
  }
}

onMounted(async () => {
  const id = Number(route.params.id)
  if (!id) return
  loading.value = true
  try {
    record.value = await reviewApi.getById(id) as any
    risks.value = record.value?.risks || []
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

/* 等高双栏布局 */
.dual-panel {
  display: flex;
  gap: 16px;
  align-items: stretch;
}
.dual-left, .dual-right {
  flex: 1;
  min-width: 0;
  display: flex;
}
.dual-left {
  flex: 14;
}
.dual-right {
  flex: 10;
}
.fill-card {
  width: 100%;
  display: flex;
  flex-direction: column;
}
.fill-card :deep(.n-card__content) {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.risk-header {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

/* 合同原文区域 */
.doc-view {
  font-size: 14px;
  line-height: 1.9;
  overflow-y: auto;
  flex: 1;
  max-height: 70vh;
}
.doc-para {
  text-indent: 2em;
  margin: 3px 0;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.2s;
}
.doc-para.doc-empty {
  text-indent: 0;
  min-height: 1.9em;
  padding: 0;
  margin: 0;
}
.doc-para.accepted {
  background: #dcfce7 !important;
  border-left: 3px solid #10b981;
}

/* 风险清单区域 */
.risk-list {
  overflow-y: auto;
  flex: 1;
  max-height: 70vh;
}
.r-item {
  padding: 12px;
  border-radius: 10px;
  margin-bottom: 8px;
}
.r-accepted {
  opacity: 0.6;
  position: relative;
}
.r-accepted::after {
  content: '✓ 已采纳';
  position: absolute;
  top: 8px;
  right: 12px;
  font-size: 12px;
  color: #10b981;
  font-weight: 600;
}
.r-critical {
  background: #fef2f2;
  border-left: 3px solid #ef4444;
}
.r-general {
  background: #fffbeb;
  border-left: 3px solid #f59e0b;
}
.r-low {
  background: #f9fafb;
  border-left: 3px solid #9ca3af;
}
.r-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.r-item p {
  font-size: 13px;
  color: var(--sl-text-2);
  margin: 4px 0;
}
.r-quote {
  font-size: 12px;
  color: var(--sl-text-3);
  padding: 6px 8px;
  background: #fafafa;
  border-radius: 6px;
  margin: 4px 0;
}
.r-fix {
  font-size: 13px;
  color: #059669;
  padding: 6px 8px;
  background: #ecfdf5;
  border-radius: 6px;
  margin: 4px 0;
}
.r-law {
  font-size: 12px;
  color: var(--sl-text-3);
}
.r-action {
  margin-top: 8px;
  display: flex;
  justify-content: flex-end;
}
</style>

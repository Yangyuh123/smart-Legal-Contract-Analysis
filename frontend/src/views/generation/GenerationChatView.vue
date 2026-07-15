<template>
  <div class="generate-page">
    <div class="gen-panels">
      <!-- 左侧表单 -->
      <div class="left-panel">
        <n-card :bordered="false" class="form-card" title="合同信息">
          <div class="type-tabs">
            <span
              v-for="t in contractTypes"
              :key="t.value"
              class="type-tab"
              :class="{ active: form.contractType === t.value }"
              @click="form.contractType = t.value"
            >
              {{ t.label }}
            </span>
          </div>

          <n-form :model="form" label-placement="top" class="info-form">
            <n-form-item label="甲方名称" required>
              <n-input v-model:value="form.partyA" placeholder="例如：XX科技有限公司" />
            </n-form-item>
            <n-form-item label="乙方名称" required>
              <n-input v-model:value="form.partyB" placeholder="例如：YY网络技术公司" />
            </n-form-item>

            <template v-if="form.contractType === 'labor'">
              <n-grid :cols="2" :x-gap="12">
                <n-gi><n-form-item label="职位"><n-input v-model:value="form.position" placeholder="高级工程师" /></n-form-item></n-gi>
                <n-gi><n-form-item label="月薪(元)"><n-input-number v-model:value="form.salary" :min="0" :step="1000" style="width:100%" /></n-form-item></n-gi>
              </n-grid>
              <n-grid :cols="2" :x-gap="12">
                <n-gi><n-form-item label="合同期限"><n-select v-model:value="form.contractTerm" :options="toOpts(termOpts)" /></n-form-item></n-gi>
                <n-gi><n-form-item label="试用期"><n-select v-model:value="form.probation" :options="toOpts(probOpts)" /></n-form-item></n-gi>
              </n-grid>
            </template>

            <template v-if="form.contractType === 'sales' || form.contractType === 'service'">
              <n-grid :cols="2" :x-gap="12">
                <n-gi><n-form-item label="合同金额(元)"><n-input-number v-model:value="form.amount" :min="0" :step="10000" style="width:100%" /></n-form-item></n-gi>
                <n-gi><n-form-item label="履行期限"><n-date-picker v-model:formatted-value="form.deadline" value-format="yyyy-MM-dd" type="date" style="width:100%" /></n-form-item></n-gi>
              </n-grid>
            </template>

            <template v-if="form.contractType === 'lease'">
              <n-grid :cols="2" :x-gap="12">
                <n-gi><n-form-item label="月租金(元)"><n-input-number v-model:value="form.rent" :min="0" :step="500" style="width:100%" /></n-form-item></n-gi>
                <n-gi><n-form-item label="押金(元)"><n-input-number v-model:value="form.deposit" :min="0" :step="500" style="width:100%" /></n-form-item></n-gi>
              </n-grid>
              <n-form-item label="租赁期限"><n-select v-model:value="form.leaseTerm" :options="toOpts(leaseOpts)" /></n-form-item>
            </template>

            <n-form-item label="补充条款要求">
              <n-input v-model:value="form.extra" type="textarea" :rows="2" placeholder="特殊条款、注意事项等（可选）" />
            </n-form-item>

            <n-button type="primary" size="large" block :loading="generating" @click="handleGenerate">
              <template #icon v-if="!generating"><n-icon :component="SparklesOutline" /></template>
              {{ generating ? '正在生成...' : '开始生成合同' }}
            </n-button>
          </n-form>
        </n-card>
      </div>

      <!-- 右侧预览 -->
      <div class="right-panel">
        <div class="preview-bar">
          <span>合同预览</span>
          <div v-if="generatedContent" style="display:flex; gap:8px;">
            <n-button size="small" @click="handleExportWord">
              <template #icon><n-icon :component="DownloadOutline" /></template>
              导出Word
            </n-button>
            <n-button size="small" type="primary" secondary @click="handleCopy">
              <template #icon><n-icon :component="CopyOutline" /></template>
              复制
            </n-button>
          </div>
        </div>
        <div class="preview-scroll">
          <div v-if="!generatedContent && !generating" class="preview-empty">
            <n-icon :size="60" :depth="4"><DocumentTextOutline /></n-icon>
            <p>填写左侧信息后点击「开始生成合同」</p>
          </div>
          <div v-if="generating && !generatedContent" class="preview-empty">
            <n-spin />
            <p>正在生成合同，请稍候...</p>
          </div>
          <div v-if="generatedContent" class="contract-content" v-html="renderMd(generatedContent)" />
        </div>
    </div>
  </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { SparklesOutline, DownloadOutline, CopyOutline, DocumentTextOutline } from '@vicons/ionicons5'
import { marked } from 'marked'

const message = useMessage()

/** 覆写 app-content 的内联样式，禁止外层滚动以保证预览区内部滚动生效 */
onMounted(() => {
  const el = document.querySelector('.app-content') as HTMLElement | null
  if (el) {
    el.style.setProperty('overflow', 'hidden', 'important')
    el.style.setProperty('padding', '0', 'important')
  }
})
onUnmounted(() => {
  const el = document.querySelector('.app-content') as HTMLElement | null
  if (el) {
    el.style.setProperty('overflow-y', 'auto', 'important')
    el.style.setProperty('padding', '24px', 'important')
  }
})
const generating = ref(false)
const generatedContent = ref('')

const contractTypes = [
  { value: 'labor', label: '劳动合同' }, { value: 'sales', label: '买卖合同' },
  { value: 'service', label: '服务合同' }, { value: 'lease', label: '租赁合同' },
  { value: 'nda', label: '保密协议' }, { value: 'cooperation', label: '合作协议' },
  { value: 'loan', label: '借款合同' }, { value: 'other', label: '其他' },
]
const termOpts = ['1年', '2年', '3年', '5年', '无固定期限']
const probOpts = ['无试用期', '1个月', '2个月', '3个月', '6个月']
const leaseOpts = ['6个月', '1年', '2年', '3年', '5年']

const toOpts = (arr: string[]) => arr.map(v => ({ label: v, value: v }))

const form = reactive({
  contractType: 'labor', partyA: '', partyB: '',
  position: '', salary: 0, contractTerm: '3年', probation: '3个月',
  amount: 0, deadline: '' as string | null, rent: 0, deposit: 0, leaseTerm: '1年', extra: '',
})

function renderMd(text: string) {
  return text ? marked.parse(text) : ''
}

function buildRequirements(): string {
  const typeLabel = contractTypes.find(t => t.value === form.contractType)?.label || '合同'
  const p = [`请生成一份${typeLabel}。甲方：${form.partyA || '甲方'}，乙方：${form.partyB || '乙方'}。`]
  if (form.contractType === 'labor') p.push(`职位：${form.position}，月薪：${form.salary}元，合同期限：${form.contractTerm}，试用期：${form.probation}。`)
  if (form.contractType === 'sales' || form.contractType === 'service') { p.push(`合同金额：${form.amount}元。`); if (form.deadline) p.push(`履行期限：${form.deadline}。`) }
  if (form.contractType === 'lease') p.push(`月租金：${form.rent}元，押金：${form.deposit}元，租赁期限：${form.leaseTerm}。`)
  if (form.extra) p.push(`补充要求：${form.extra}。`)
  p.push('请生成完整规范的合同条款，Markdown格式，包含双方信息、核心条款、违约责任、争议解决等内容。')
  return p.join('')
}

async function handleGenerate() {
  if (!form.partyA || !form.partyB) {
    message.warning('请填写甲乙双方名称')
    return
  }
  generating.value = true
  generatedContent.value = ''
  const typeLabel = contractTypes.find(t => t.value === form.contractType)?.label || '合同'

  try {
    const token = localStorage.getItem('access_token')
    const resp = await fetch('/api/v1/generation/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ contractType: typeLabel, requirements: buildRequirements(), partyA: form.partyA, partyB: form.partyB }),
    })
    if (!resp.ok) throw new Error('请求失败: HTTP ' + resp.status)
    if (!resp.body) throw new Error('浏览器不支持流式响应')

    const reader = resp.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let partial = ''
    let streamDone = false

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      partial += decoder.decode(value, { stream: true })
      const events = partial.split('\n\n')
      partial = events.pop() || ''
      for (const event of events) {
        for (const line of event.split('\n')) {
          if (line.trim() === 'data: [DONE]') {
            streamDone = true
            break
          }
          parseLine(line)
        }
        if (streamDone) break
      }
      if (streamDone) break
    }
  } catch (e: any) {
    message.error('生成失败: ' + (e.message || '未知错误'))
  } finally {
    generating.value = false
  }
}

function parseLine(line: string) {
  const trimmed = line.trim()
  if (!trimmed.startsWith('data:')) return
  const jsonStr = trimmed.slice(5).trim()
  if (!jsonStr || jsonStr === '[DONE]') return
  try {
    generatedContent.value += JSON.parse(jsonStr).content
  } catch { /* skip malformed */ }
}

function handleExportWord() {
  const blob = new Blob([generatedContent.value], { type: 'application/msword' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `${form.partyA}_${form.partyB}_合同.doc`
  a.click()
}

function handleCopy() {
  navigator.clipboard.writeText(generatedContent.value).then(() => message.success('已复制'))
}
</script>

<style scoped>
.generate-page {
  height: calc(100vh - 60px);
  overflow: hidden;
}
.gen-panels {
  display: flex;
  gap: 16px;
  height: 100%;
  padding: 16px;
  box-sizing: border-box;
}
.left-panel {
  flex: 10;
  min-width: 0;
  height: 100%;
  overflow-y: auto;
}
.right-panel {
  flex: 14;
  min-width: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 8px;
  border: 1px solid var(--sl-border);
}
.form-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.form-card :deep(.n-card__content) {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}
.preview-bar {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 20px; border-bottom: 1px solid var(--sl-border);
  font-size: 16px; font-weight: 600; flex-shrink: 0;
}
.preview-scroll {
  flex: 1; overflow: auto; padding: 0; overflow-x: hidden;
}
.type-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
}
.type-tab {
  padding: 6px 14px;
  border: 1px solid var(--sl-border);
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: var(--sl-text-2);
  transition: all 0.2s;
}
.type-tab:hover {
  border-color: var(--sl-primary);
  color: var(--sl-primary);
}
.type-tab.active {
  background: var(--sl-primary);
  color: #fff;
  border-color: var(--sl-primary);
}
.preview-empty {
  text-align: center;
  padding: 80px 20px;
  color: var(--sl-text-3);
  margin: auto;
}
.preview-empty p {
  margin-top: 16px;
  font-size: 15px;
}
.contract-content {
  padding: 16px 20px;
  line-height: 1.9;
  font-size: 14px;
  color: var(--sl-text-1);
  word-break: break-all;
  overflow-wrap: break-word;
  max-width: 100%;
}
.contract-content :deep(h2) {
  text-align: center;
  font-size: 20px;
  margin-bottom: 20px;
}
.contract-content :deep(h3) {
  font-size: 16px;
  margin: 16px 0 8px;
}
.contract-content :deep(p) {
  text-indent: 2em;
  margin: 6px 0;
}
.contract-content :deep(blockquote) {
  border-left: 3px solid var(--sl-primary);
  padding: 4px 12px;
  background: var(--sl-primary-soft);
  margin: 8px 0;
}
</style>

<template>
  <div class="generate-page">
    <div class="gen-panels">
      <section class="chat-panel">
        <div class="panel-header">
          <div>
            <div class="panel-title">合同生成助手</div>
            <div class="panel-subtitle">AI 通过自然语言追问关键信息，再生成标准、合规的合同文本</div>
          </div>
          <n-tag size="small" :type="canGenerate ? 'success' : 'info'" round>
            {{ canGenerate ? '可生成' : 'AI问答' }}
          </n-tag>
        </div>

        <div ref="chatScrollRef" class="chat-scroll">
          <div
            v-for="message in messages"
            :key="message.id"
            class="chat-row"
            :class="`chat-row-${message.role}`"
          >
            <div class="chat-bubble">
              <div class="chat-name">{{ message.role === 'assistant' ? 'AI 助手' : '我' }}</div>
              <div
                v-if="chatStreaming && streamingMessageId === message.id && !message.content"
                class="waiting-dots"
                aria-label="AI is thinking"
              >
                <span />
                <span />
                <span />
              </div>
              <div v-else class="chat-text">{{ message.content }}</div>
              <span v-if="chatStreaming && streamingMessageId === message.id" class="typing-cursor" />
            </div>
          </div>
        </div>

        <div class="quick-actions">
          <n-button
            v-for="option in starterOptions"
            :key="option"
            size="small"
            secondary
            :disabled="busy || hasUserMessage"
            @click="sendUserMessage(option)"
          >
            {{ option }}
          </n-button>
        </div>

        <div class="input-bar">
          <n-input
            ref="inputRef"
            v-model:value="draft"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 4 }"
            placeholder="直接描述你的合同需求，或回答 AI 的问题。Enter 发送，Shift+Enter 换行"
            :disabled="busy"
            @keydown.enter.exact.prevent="submitDraft"
          />
          <div class="input-actions">
            <n-button secondary :disabled="busy" @click="resetConversation">重新开始</n-button>
            <n-button
              type="primary"
              secondary
              :disabled="busy || !draft.trim()"
              @click="submitDraft"
            >
              发送给 AI
            </n-button>
            <n-button
              type="primary"
              :loading="generating"
              :disabled="chatStreaming || !canGenerate"
              @click="handleGenerate"
            >
              {{ generating ? '正在生成...' : '生成合同' }}
            </n-button>
          </div>
        </div>
      </section>

      <section class="preview-panel">
        <div class="preview-bar">
          <span>合同预览</span>
          <div v-if="generatedContent" class="preview-actions">
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

        <div ref="previewScrollRef" class="preview-scroll">
          <div v-if="!generatedContent && !generating" class="preview-empty">
            <n-icon :size="58" :depth="4"><DocumentTextOutline /></n-icon>
            <p>和 AI 完成信息确认后，点击“生成合同”查看结果</p>
          </div>
          <div v-if="generating && !generatedContent" class="preview-empty">
            <n-spin />
            <p>正在起草合同，请稍候...</p>
          </div>
          <div v-if="generatedContent" class="contract-content" v-html="renderMd(generatedContent)" />
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { useMessage, type InputInst } from 'naive-ui'
import { CopyOutline, DocumentTextOutline, DownloadOutline } from '@vicons/ionicons5'
import { marked } from 'marked'

type Role = 'assistant' | 'user'

interface ChatMessage {
  id: number
  role: Role
  content: string
}

const message = useMessage()

marked.setOptions({ breaks: true, gfm: true })

const starterOptions = ['买卖合同', '服务合同', '劳动合同', '租赁合同', '保密协议']
const initialAssistantMessage = '你好，我会通过几轮问答帮你补齐合同关键信息。请先告诉我：你要生成什么类型的合同？也可以直接完整描述你的需求。'
const readyMarker = '【可生成】'
const pendingMarker = '【继续补充】'
const draft = ref('')
const chatStreaming = ref(false)
const generating = ref(false)
const generatedContent = ref('')
const streamingMessageId = ref<number | null>(null)
const chatScrollRef = ref<HTMLElement | null>(null)
const previewScrollRef = ref<HTMLElement | null>(null)
const inputRef = ref<InputInst | null>(null)
const messages = ref<ChatMessage[]>([
  {
    id: 1,
    role: 'assistant',
    content: initialAssistantMessage,
  },
])

onMounted(() => {
  focusInput()
})

const busy = computed(() => chatStreaming.value || generating.value)
const hasUserMessage = computed(() => messages.value.some(item => item.role === 'user'))
const canGenerate = computed(() =>
  isReadyAssistantMessage([...messages.value].reverse().find(item => item.role === 'assistant')?.content || '')
)

function isReadyAssistantMessage(content: string) {
  const normalized = content.trim()
  const blockers = ['信息不足', '无法', '不能', '不可', '还缺', '缺少', '请先', '需要补充', '不足以']
  return normalized.startsWith(readyMarker) && !blockers.some(word => normalized.includes(word))
}

function renderMd(text: string) {
  return text ? marked.parse(text) : ''
}

function submitDraft() {
  sendUserMessage(draft.value)
}

async function sendUserMessage(value: string) {
  const trimmed = value.trim()
  if (!trimmed || busy.value) return

  pushMessage('user', trimmed)
  draft.value = ''
  await streamAssistantReply(trimmed)
}

function pushMessage(role: Role, content: string) {
  messages.value.push({ id: Date.now() + messages.value.length, role, content })
  scrollChatToBottom()
}

function updateMessage(id: number, append: string) {
  const target = messages.value.find(item => item.id === id)
  if (target) target.content += append
  scrollChatToBottom()
}

function scrollChatToBottom() {
  nextTick(() => {
    if (chatScrollRef.value) {
      chatScrollRef.value.scrollTop = chatScrollRef.value.scrollHeight
    }
  })
}

function scrollPreviewToBottom() {
  nextTick(() => {
    if (previewScrollRef.value) {
      previewScrollRef.value.scrollTop = previewScrollRef.value.scrollHeight
    }
  })
}

function focusInput() {
  nextTick(() => {
    inputRef.value?.focus()
  })
}

function buildChatInstruction(latestMessage: string) {
  return [
    `输出规则：信息不足时必须以 ${pendingMarker} 开头，并只追问一个最重要的问题；信息足够时才允许以 ${readyMarker} 开头。`,
    `禁止在包含“信息不足、无法、不能、还缺、请先、需要补充”等意思的回复中使用 ${readyMarker}。`,
    '最低生成条件：合同类型、甲方、乙方、合同标的、价款或报酬、期限、履行/交付/验收方式、违约责任、争议解决方式均已有基本信息。',
    `只有当信息足够生成合同时，回复开头必须使用 ${readyMarker}；信息不足时绝对不要使用这个标记。`,
    '你是一个合同生成前的信息采集助手。你的任务是用自然语言对话引导用户补齐生成标准、合规合同所需信息。',
    '请根据对话历史判断还缺什么关键信息。每次回复最多只问 1 个最重要的问题，语言简洁。',
    '通常需要确认：合同类型、甲方、乙方、合同标的、金额或报酬、期限、履行/交付/验收、违约责任、争议解决、保密或知识产权等特殊要求。',
    '如果信息已经足够生成合同，请先用 5-8 条简要汇总已确认信息，再提示用户点击“生成合同”。',
    '不要在问答阶段直接输出完整合同。',
    '',
    `用户最新输入：${latestMessage}`,
  ].join('\n')
}

function buildContractRequirements() {
  const conversationText = messages.value
    .map(item => `${item.role === 'user' ? '用户' : 'AI助手'}：${item.content}`)
    .join('\n\n')

  return [
    '请根据以下自然语言问答记录，生成一份标准、完整、合规的中文合同。',
    '要求：条款结构清晰，包含主体信息、合同标的、价款或报酬、履行期限、交付验收、权利义务、保密、知识产权（如适用）、违约责任、不可抗力、争议解决、生效与签署等必要条款。',
    '如对话中未提供证件号、地址、联系方式等细节，请使用【待补充】标记，不要编造。',
    '如果存在明显不合规或约定不清的内容，请在合同相应条款中采用更稳妥、合法、可执行的表述。',
    '',
    '问答记录：',
    conversationText,
  ].join('\n')
}

function inferContractType() {
  const text = messages.value.map(item => item.content).join(' ')
  const found = starterOptions.find(option => text.includes(option))
  return found || '合同'
}

function inferParty(label: '甲方' | '乙方') {
  const text = messages.value.map(item => item.content).join('\n')
  const match = text.match(new RegExp(`${label}[：:是为]?\\s*([^，。；;\\n]+)`))
  return match?.[1]?.trim() || label
}

async function streamAssistantReply(latestMessage: string) {
  chatStreaming.value = true
  const assistantId = Date.now() + messages.value.length
  streamingMessageId.value = assistantId
  messages.value.push({ id: assistantId, role: 'assistant', content: '' })
  scrollChatToBottom()

  try {
    await streamGeneration({
      contractType: inferContractType(),
      partyA: inferParty('甲方'),
      partyB: inferParty('乙方'),
      requirements: buildChatInstruction(latestMessage),
      conversation: messages.value
        .filter(item => item.id !== assistantId)
        .map(item => ({ role: item.role, content: item.content })),
      onContent: chunk => updateMessage(assistantId, chunk),
    })
  } catch (e: any) {
    updateMessage(assistantId, `抱歉，AI 问答失败：${e.message || '未知错误'}`)
  } finally {
    chatStreaming.value = false
    streamingMessageId.value = null
    focusInput()
  }
}

async function handleGenerate() {
  if (!canGenerate.value) {
    message.warning('请先根据 AI 的问题补充信息，等 AI 确认可生成后再生成合同')
    return
  }

  generating.value = true
  generatedContent.value = ''
  scrollPreviewToBottom()

  try {
    await streamGeneration({
      contractType: inferContractType(),
      partyA: inferParty('甲方'),
      partyB: inferParty('乙方'),
      requirements: buildContractRequirements(),
      onContent: chunk => {
        generatedContent.value += chunk
        scrollPreviewToBottom()
      },
    })
  } catch (e: any) {
    message.error(`生成失败：${e.message || '未知错误'}`)
  } finally {
    generating.value = false
    focusInput()
  }
}

async function streamGeneration(options: {
  contractType: string
  partyA: string
  partyB: string
  requirements: string
  conversation?: Array<{ role: Role; content: string }>
  onContent: (chunk: string) => void
}) {
  const token = localStorage.getItem('access_token')
  const resp = await fetch('/api/v1/generation/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      contractType: options.contractType,
      requirements: options.requirements,
      partyA: options.partyA,
      partyB: options.partyB,
      conversation: options.conversation,
    }),
  })

  if (!resp.ok) throw new Error(`请求失败：HTTP ${resp.status}`)
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
        parseLine(line, options.onContent)
      }
      if (streamDone) break
    }
    if (streamDone) break
  }
}

function parseLine(line: string, onContent: (chunk: string) => void) {
  const trimmed = line.trim()
  if (!trimmed.startsWith('data:')) return

  const jsonStr = trimmed.slice(5).trim()
  if (!jsonStr || jsonStr === '[DONE]') return

  try {
    const payload = JSON.parse(jsonStr)
    if (payload.content) onContent(payload.content)
    if (payload.error) message.error(payload.error)
  } catch {
    // Ignore malformed SSE fragments.
  }
}

function resetConversation() {
  draft.value = ''
  generatedContent.value = ''
  chatStreaming.value = false
  generating.value = false
  streamingMessageId.value = null
  messages.value = [{ id: 1, role: 'assistant', content: initialAssistantMessage }]
  focusInput()
}

function handleExportWord() {
  const blob = new Blob([generatedContent.value], { type: 'application/msword;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `${inferParty('甲方')}_${inferParty('乙方')}_${inferContractType()}.doc`
  a.click()
  URL.revokeObjectURL(a.href)
}

function handleCopy() {
  navigator.clipboard.writeText(generatedContent.value).then(() => message.success('已复制'))
}
</script>

<style scoped>
.generate-page {
  --app-header-height: 60px;
  --app-content-y-padding: 48px;
  height: calc(100vh - var(--app-header-height) - var(--app-content-y-padding));
  max-height: calc(100vh - var(--app-header-height) - var(--app-content-y-padding));
  overflow: hidden;
}

.gen-panels {
  display: grid;
  grid-template-columns: minmax(360px, 0.9fr) minmax(420px, 1.1fr);
  gap: 16px;
  height: 100%;
  padding: 16px;
  box-sizing: border-box;
}

.chat-panel,
.preview-panel {
  min-width: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
  border: 1px solid var(--sl-border);
  border-radius: 8px;
  overflow: hidden;
}

.panel-header,
.preview-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 18px;
  border-bottom: 1px solid var(--sl-border);
  flex-shrink: 0;
}

.panel-title,
.preview-bar {
  font-size: 16px;
  font-weight: 600;
  color: var(--sl-text-1);
}

.panel-subtitle {
  margin-top: 4px;
  font-size: 13px;
  color: var(--sl-text-3);
}

.chat-scroll,
.preview-scroll {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

.chat-scroll {
  padding: 18px;
  background: #f8fafc;
}

.chat-row {
  display: flex;
  margin-bottom: 14px;
}

.chat-row-user {
  justify-content: flex-end;
}

.chat-bubble {
  max-width: 82%;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  background: #fff;
  color: var(--sl-text-1);
  line-height: 1.7;
  word-break: break-word;
}

.chat-row-user .chat-bubble {
  color: #fff;
  background: var(--sl-primary);
  border-color: var(--sl-primary);
}

.chat-name {
  margin-bottom: 4px;
  font-size: 12px;
  font-weight: 600;
  opacity: 0.72;
}

.chat-text {
  display: inline;
  white-space: pre-wrap;
  font-size: 14px;
}

.waiting-dots {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 20px;
}

.waiting-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--sl-primary);
  opacity: 0.35;
  animation: waiting-dot 1s infinite ease-in-out;
}

.waiting-dots span:nth-child(2) {
  animation-delay: 0.15s;
}

.waiting-dots span:nth-child(3) {
  animation-delay: 0.3s;
}

.typing-cursor {
  display: inline-block;
  width: 2px;
  height: 1em;
  margin-left: 2px;
  vertical-align: text-bottom;
  background: var(--sl-primary);
  animation: blink 0.8s infinite;
}

.quick-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  min-height: 42px;
  padding: 10px 16px 0;
  border-top: 1px solid var(--sl-border);
}

.input-bar {
  padding: 12px 16px 16px;
  background: #fff;
  flex-shrink: 0;
}

.input-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 10px;
}

.preview-actions {
  display: flex;
  gap: 8px;
}

.preview-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 360px;
  color: var(--sl-text-3);
  text-align: center;
}

.preview-empty p {
  margin-top: 16px;
  font-size: 15px;
}

.contract-content {
  padding: 18px 24px;
  max-width: 100%;
  color: var(--sl-text-1);
  font-size: 14px;
  line-height: 1.9;
  word-break: break-word;
  overflow-wrap: break-word;
}

.contract-content :deep(h1),
.contract-content :deep(h2) {
  text-align: center;
  font-size: 22px;
  margin: 10px 0 22px;
}

.contract-content :deep(h3) {
  font-size: 16px;
  margin: 18px 0 8px;
}

.contract-content :deep(p) {
  margin: 6px 0;
}

.contract-content :deep(ul),
.contract-content :deep(ol) {
  padding-left: 24px;
}

@keyframes blink {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0;
  }
}

@keyframes waiting-dot {
  0%,
  80%,
  100% {
    opacity: 0.35;
    transform: translateY(0);
  }
  40% {
    opacity: 1;
    transform: translateY(-4px);
  }
}

@media (max-width: 980px) {
  .generate-page {
    height: calc(100vh - var(--app-header-height) - var(--app-content-y-padding));
    max-height: calc(100vh - var(--app-header-height) - var(--app-content-y-padding));
    overflow: hidden;
  }

  .gen-panels {
    grid-template-columns: 1fr;
    grid-template-rows: minmax(0, 1fr) minmax(0, 1fr);
    height: 100%;
  }

  .chat-panel,
  .preview-panel {
    height: 100%;
  }
}
</style>

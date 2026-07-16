<template>
  <div class="generate-page">
    <div class="gen-panels">
      <section class="chat-panel">
        <div class="panel-header">
          <div>
            <div class="panel-title">合同生成助手</div>
            <div class="panel-subtitle">
              <template v-if="editMode">合同已生成，在下方输入修改需求来调整合同内容</template>
              <template v-else>快速确认关键信息，先生成模板再通过对话修改</template>
            </div>
          </div>
          <n-tag size="small" :type="editMode ? 'warning' : canGenerate ? 'success' : 'info'" round>
            {{ editMode ? '编辑模式' : canGenerate ? '可生成' : 'AI问答' }}
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
          <!-- 编辑模式：显示修改建议 -->
          <template v-if="editMode">
            <n-button
              v-for="option in editStarterOptions"
              :key="option"
              size="small"
              secondary
              type="warning"
              :disabled="busy"
              @click="sendUserMessage(option)"
            >
              {{ option }}
            </n-button>
          </template>
          <!-- 问答模式：显示合同类型 -->
          <template v-else>
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
          </template>
        </div>

        <div class="input-bar">
          <n-input
            ref="inputRef"
            v-model:value="draft"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 4 }"
            :placeholder="editMode
              ? '描述你想要的修改，例如：把违约金从5%改成10%、添加不可抗力条款、删除第3条... Enter 发送，Shift+Enter 换行'
              : '直接描述你的合同需求，或回答 AI 的问题。Enter 发送，Shift+Enter 换行'"
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
              {{ editMode ? '发送修改需求' : '发送给 AI' }}
            </n-button>
            <n-button
              v-if="!editMode"
              type="primary"
              :loading="generating"
              :disabled="chatStreaming || !canGenerate"
              @click="handleGenerate"
            >
              {{ generating ? '正在生成...' : '生成合同' }}
            </n-button>
            <n-tag v-else type="warning" size="large" round>
              编辑模式中 — 输入修改需求后发送
            </n-tag>
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
import { useDialog, useMessage, type InputInst } from 'naive-ui'
import { CopyOutline, DocumentTextOutline, DownloadOutline } from '@vicons/ionicons5'
import { marked } from 'marked'

type Role = 'assistant' | 'user'

interface ChatMessage {
  id: number
  role: Role
  content: string
}

const message = useMessage()
const dialog = useDialog()

marked.setOptions({ breaks: true, gfm: true })

/** 统计合同中【待补充】标记的数量 */
function countPlaceholders(text: string): number {
  return (text.match(/【待补充】/g) || []).length
}

/** 检查合同是否还包含【待补充】标记 */
function hasPlaceholders(text: string): boolean {
  return text.includes('【待补充】')
}

const starterOptions = ['买卖合同', '服务合同', '劳动合同', '租赁合同', '保密协议']
const editStarterOptions = ['补充待补充信息', '修改违约金条款', '添加保密条款', '调整付款方式', '修改争议解决方式']
const initialAssistantMessage = '你好！请直接告诉我你要生成什么类型的合同，以及甲方、乙方分别是谁。我会快速生成一份合同模板，你可以在预览中查看并通过对话继续修改细节。'
const readyMarker = '【可生成】'
const pendingMarker = '【继续补充】'
const draft = ref('')
const chatStreaming = ref(false)
const generating = ref(false)
const generatedContent = ref('')
const editMode = ref(false)
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
  if (!text) return ''
  // 将【待补充】替换为红色高亮的 HTML 标签
  const highlighted = text.replace(
    /【待补充】/g,
    '<span class="placeholder-tag">【待补充】</span>',
  )
  return marked.parse(highlighted) as string
}

function submitDraft() {
  sendUserMessage(draft.value)
}

async function sendUserMessage(value: string) {
  const trimmed = value.trim()
  if (!trimmed || busy.value) return

  // 编辑模式：用户消息用于修改已生成的合同
  if (editMode.value) {
    await handleEditRequest(trimmed)
    return
  }

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
    '你是一个合同生成助手。核心理念：快速生成模板，让用户在预览中看到合同后通过对话修改。',
    '',
    `输出规则：`,
    `- 如果用户已提供合同类型和双方主体，立即以 ${readyMarker} 开头回复，简要汇总已确认信息（2-4条），然后提示用户点击”生成合同”。`,
    `- 即使用户信息不完整（如缺少金额、期限、违约责任等），也应以 ${readyMarker} 开头，缺失信息用【待补充】标记即可——模板生成后用户可以继续修改。`,
    `- 只在用户连合同类型都没说清楚时，才以 ${pendingMarker} 开头追问，且最多追问1个问题。`,
    `- 绝不追问超过1个问题。信息不足不是问题——先生成模板再说。`,
    `- 禁止在问答阶段输出完整合同。`,
    '',
    `最低生成条件（满足即可标记${readyMarker}）：`,
    '- 合同类型已明确',
    '- 甲方和乙方已明确（可以是简称或描述，如”某科技公司”）',
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

function buildEditInstruction(userRequest: string, currentContract: string) {
  return [
    '你是一个合同编辑助手。用户正在查看一份已生成的合同，并希望通过自然语言对话来修改它。',
    '请根据用户的修改需求，修改以下合同，并返回修改后的完整合同文本。',
    '',
    '修改原则：',
    '1. 仅修改用户要求的部分，保持其他条款内容不变',
    '2. 如果修改影响其他条款的一致性（如金额、日期、名称等跨条款引用），自动做相应调整',
    '3. 对于用户没有明确但修改后可能涉及的细节，使用更稳妥、合法、可执行的表述',
    '4. 如果用户的要求在法律上存在风险，在合同相应位置添加必要的保护性条款',
    '5. 直接返回修改后的完整合同文本，不要添加任何解释、说明或问候语',
    '6. 不要在合同前后加"以下是修改后的合同"之类的引导语——直接输出合同正文',
    '',
    '当前合同内容：',
    currentContract || '(空)',
    '',
    '用户修改需求：',
    userRequest,
    '',
    '请返回修改后的完整合同文本。',
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
    // 生成成功，进入编辑模式
    editMode.value = true
    const placeholderCount = countPlaceholders(generatedContent.value)
    if (placeholderCount > 0) {
      pushMessage('assistant', `合同模板已生成！📋 有 ${placeholderCount} 处【待补充】标记（预览中红色高亮），建议尽快补充完整。你可以直接告诉我这些内容，例如"违约金设为20%"、"争议解决选北京仲裁委员会"等。`)
    } else {
      pushMessage('assistant', '合同模板已生成，所有信息已补充完整！如需调整任何条款，直接告诉我即可，例如"把违约金改成20%"、"添加保密条款"等。')
    }
    message.success('合同模板生成成功，现在可以通过对话修改合同')
  } catch (e: any) {
    message.error(`生成失败：${e.message || '未知错误'}`)
  } finally {
    generating.value = false
    focusInput()
  }
}

async function handleEditRequest(userMessage: string) {
  const trimmed = userMessage.trim()
  if (!trimmed || busy.value) return

  // 保存修改前的合同内容（用于回退，暂不实现UI）
  pushMessage('user', trimmed)
  draft.value = ''

  generating.value = true
  const oldContent = generatedContent.value
  generatedContent.value = ''

  try {
    await streamGeneration({
      contractType: inferContractType(),
      partyA: inferParty('甲方'),
      partyB: inferParty('乙方'),
      requirements: buildEditInstruction(trimmed, oldContent),
      onContent: chunk => {
        generatedContent.value += chunk
        scrollPreviewToBottom()
      },
    })
    // 编辑完成后在聊天中给出简短确认，并提示剩余待补充
    const remainingCount = countPlaceholders(generatedContent.value)
    if (remainingCount > 0) {
      pushMessage('assistant', `合同已更新。📋 仍有 ${remainingCount} 处【待补充】标记（红色高亮），建议继续补充。你可以直接告诉我缺失的信息，我来帮你完善。`)
    } else {
      pushMessage('assistant', '合同已更新，所有信息已补充完整！如需继续修改，请直接告诉我。')
    }
    message.success('合同已更新')
  } catch (e: any) {
    generatedContent.value = oldContent // 失败时恢复原内容
    pushMessage('assistant', `修改失败：${e.message || '未知错误'}，合同内容已恢复。`)
    message.error(`修改失败：${e.message || '未知错误'}`)
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
  editMode.value = false
  streamingMessageId.value = null
  messages.value = [{ id: 1, role: 'assistant', content: initialAssistantMessage }]
  focusInput()
}

function handleExportWord() {
  if (hasPlaceholders(generatedContent.value)) {
    const count = countPlaceholders(generatedContent.value)
    dialog.warning({
      title: '合同未补充完整',
      content: `合同中仍有 ${count} 处【待补充】标记（已在预览中红色高亮标注）。建议补充完整后再导出，以确保合同的完整性和法律效力。确定要继续导出吗？`,
      positiveText: '继续导出',
      negativeText: '返回补充',
      onPositiveClick: () => doExportWord(),
    })
    return
  }
  doExportWord()
}

function doExportWord() {
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

/* 【待补充】红色高亮标记 */
.contract-content :deep(.placeholder-tag) {
  color: #e53e3e;
  background: #fff5f5;
  border: 1px solid #fc8181;
  border-radius: 3px;
  padding: 1px 5px;
  font-weight: 700;
  white-space: nowrap;
  animation: placeholder-pulse 2s ease-in-out infinite;
}

@keyframes placeholder-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
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

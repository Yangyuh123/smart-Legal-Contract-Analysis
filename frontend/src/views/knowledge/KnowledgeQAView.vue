<template>
  <div class="qa-page sl-page">
    <div class="sl-flex-between" style="margin-bottom: 20px;">
      <div>
        <div class="sl-page-title">智能问答</div>
        <div class="sl-page-subtitle">基于已上传的法律知识库文档进行检索增强生成（RAG）问答</div>
      </div>
      <n-button @click="router.push('/knowledge')">
        <template #icon><n-icon :component="FolderOpenOutline" /></template>
        知识库管理
      </n-button>
    </div>

    <n-card :bordered="false" class="qa-card">
      <div class="qa-scroll"><div class="qa-messages" ref="msgBox">
        <div v-if="messages.length === 0" class="qa-empty">
          <n-icon :size="56" :depth="4"><ChatbubbleEllipsesOutline /></n-icon>
          <p>基于法律知识库的智能问答</p>
          <div class="examples">
            <n-tag
              v-for="q in examples"
              :key="q"
              class="ex-tag"
              round
              :bordered="false"
              @click="ask(q)"
            >
              {{ q }}
            </n-tag>
          </div>
        </div>
        <div v-for="(m, i) in messages" :key="i" class="qa-msg" :class="'qa-' + m.role">
          <div class="qa-role">{{ m.role === 'user' ? '我' : '知识库助手' }}</div>
          <div class="qa-content" v-html="renderMd(m.content)" />
        </div>
      </div>

      </div>
      <div class="qa-input">
        <n-input-group>
          <n-input
            v-model:value="question"
            placeholder="输入法律问题，系统将基于知识库文档回答..."
            :disabled="streaming"
            size="large"
            @keyup.enter="ask(question)"
          />
          <n-button
            type="primary"
            size="large"
            :loading="streaming"
            :disabled="!question.trim()"
            @click="ask(question)"
          >
            {{ streaming ? '检索中' : '提问' }}
          </n-button>
        </n-input-group>
      </div>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ChatbubbleEllipsesOutline, FolderOpenOutline } from '@vicons/ionicons5'
import { marked } from 'marked'

const router = useRouter()
const question = ref('')
const streaming = ref(false)
const messages = ref<Array<{ role: string; content: string }>>([])
const msgBox = ref<HTMLElement>()

const examples = [
  '《劳动合同法》对试用期有哪些规定？',
  '合同违约金的计算标准是什么？',
  '什么是格式条款？什么情况下无效？',
  '保密协议的期限一般多久？',
  '竞业限制的适用条件和补偿标准',
]

function renderMd(text: string) {
  return text ? marked.parse(text) : ''
}

function scrollBottom() {
  nextTick(() => {
    if (msgBox.value) msgBox.value.scrollTop = msgBox.value.scrollHeight
  })
}

async function ask(q: string) {
  const text = (typeof q === 'string' ? q : question.value).trim()
  if (!text || streaming.value) return
  if (typeof q === 'string') question.value = ''

  messages.value.push({ role: 'user', content: text })
  messages.value.push({ role: 'assistant', content: '' })
  const ai = messages.value.length - 1
  streaming.value = true
  scrollBottom()

  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 60000)

  try {
    const token = localStorage.getItem('access_token')
    const resp = await fetch('/api/v1/knowledge/qa', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ question: text }),
      signal: controller.signal,
    })
    if (!resp.ok) throw new Error('请求失败: HTTP ' + resp.status)
    if (!resp.body) throw new Error('不支持流式响应')

    const reader = resp.body.getReader()
    const dec = new TextDecoder()
    let partial = ''
    let streamDone = false

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      partial += dec.decode(value, { stream: true })
      const events = partial.split('\n\n')
      partial = events.pop() || ''
      for (const event of events) {
        for (const line of event.split('\n')) {
          const trimmed = line.trim()
          if (!trimmed.startsWith('data:')) continue
          const jsonStr = trimmed.slice(5).trim()
          if (!jsonStr) continue
          if (jsonStr === '[DONE]') { streamDone = true; break }
          try {
            const obj = JSON.parse(jsonStr)
            const chunk = obj.content || obj.data || ''
            if (chunk) messages.value[ai].content += chunk
          } catch { /* skip malformed */ }
        }
        if (streamDone) break
      }
      if (streamDone) break
      scrollBottom()
    }
  } catch (e: any) {
    if (e.name !== 'AbortError') messages.value[ai].content = '回答生成失败，请重试'
  } finally {
    clearTimeout(timeout)
    streaming.value = false
    // 过滤"根据参考的第X条"等提示文字
    messages.value[ai].content = messages.value[ai].content
        .replace(/根据.{0,10}参考.{0,20}第?\d+条.{0,10}[，,。\.\s]*/g, '')
        .replace(/以上回答基于AI知识库[\s\S]*/g, '')
  }
}
</script>

<style scoped>
.qa-scroll {
  height: calc(100vh - 320px);
  overflow-y: auto;
  padding: 0 4px;
}
.qa-card {
  display: flex;
  flex-direction: column;
}
.qa-messages {
  padding: 8px 0;
}
.qa-empty {
  text-align: center;
  padding: 70px 20px;
  color: var(--sl-text-3);
}
.qa-empty p {
  margin-top: 12px;
  font-size: 15px;
}
.examples {
  margin-top: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}
.ex-tag {
  cursor: pointer;
  background: var(--sl-primary-soft) !important;
  color: var(--sl-primary) !important;
}
.qa-msg {
  margin-bottom: 18px;
}
.qa-role {
  font-size: 12px;
  color: var(--sl-text-3);
  margin-bottom: 4px;
}
.qa-content {
  padding: 12px 16px;
  border-radius: 10px;
  background: var(--sl-bg-soft);
  line-height: 1.7;
  font-size: 14px;
}
.qa-user .qa-content {
  background: var(--sl-primary-soft);
}
.qa-content :deep(p) {
  margin: 4px 0;
}
.qa-content :deep(ul),
.qa-content :deep(ol) {
  padding-left: 20px;
  margin: 4px 0;
}
.qa-content :deep(blockquote) {
  border-left: 3px solid var(--sl-primary);
  padding: 4px 12px;
  margin: 4px 0;
  background: var(--sl-primary-soft);
}
.qa-input {
  padding-top: 12px;
  border-top: 1px solid var(--sl-border);
}
</style>

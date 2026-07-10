<template>
  <div
    class="chat-message"
    :class="[
      `chat-message--${message.role}`,
      { 'chat-message--streaming': isStreaming && message.role === 'assistant' }
    ]"
  >
    <!-- 头像 -->
    <div class="chat-message__avatar">
      <el-avatar
        :size="36"
        :class="`chat-message__avatar--${message.role}`"
      >
        <el-icon v-if="message.role === 'user'" :size="20"><UserFilled /></el-icon>
        <el-icon v-else :size="20"><Service /></el-icon>
      </el-avatar>
    </div>

    <!-- 消息主体 -->
    <div class="chat-message__body">
      <!-- 消息发送者标签 -->
      <div class="chat-message__sender">
        <span class="chat-message__sender-name">
          {{ message.role === 'user' ? '我' : 'AI 助手' }}
        </span>
        <span class="chat-message__time">{{ formattedTime }}</span>
      </div>

      <!-- 消息内容 -->
      <div class="chat-message__bubble">
        <!-- 用户消息：纯文本 -->
        <div v-if="message.role === 'user'" class="chat-message__text">
          {{ message.content }}
        </div>

        <!-- AI 消息：渲染 Markdown -->
        <div
          v-else
          class="chat-message__markdown markdown-content"
          v-html="renderedContent"
        ></div>

        <!-- 流式输出指示器 -->
        <span
          v-if="isStreaming && message.role === 'assistant'"
          class="chat-message__cursor"
        ></span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { UserFilled, Service } from '@element-plus/icons-vue'
import { marked } from 'marked'
import type { ChatMessage } from '@/types/generation'
import { formatDate } from '@/utils/format'

// Configure marked for safe rendering
marked.setOptions({
  breaks: true,
  gfm: true,
})

interface Props {
  message: ChatMessage
  isStreaming?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isStreaming: false,
})

/** Render markdown to HTML */
const renderedContent = computed(() => {
  if (!props.message.content) return ''
  try {
    return marked.parse(props.message.content) as string
  } catch {
    return `<p>${props.message.content}</p>`
  }
})

/** Format timestamp */
const formattedTime = computed(() => {
  if (!props.message.timestamp) return ''
  try {
    return formatDate(props.message.timestamp)
  } catch {
    return props.message.timestamp
  }
})
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.chat-message {
  display: flex;
  gap: $spacing-md;
  padding: $spacing-sm $spacing-base;
  animation: message-appear 0.3s $transition-ease-out;

  // 用户消息：右对齐
  &--user {
    flex-direction: row-reverse;

    .chat-message__sender {
      flex-direction: row-reverse;
      text-align: right;
    }

    .chat-message__bubble {
      background-color: $color-primary;
      color: $color-white;
      border-radius: $radius-lg 4px $radius-lg $radius-lg;
    }

    .chat-message__text {
      color: $color-white;
    }
  }

  // AI 消息：左对齐
  &--assistant {
    .chat-message__bubble {
      background-color: $color-gray-50;
      color: $color-text-primary;
      border: 1px solid $color-gray-200;
      border-radius: 4px $radius-lg $radius-lg $radius-lg;
    }
  }

  // 流式输出中
  &--streaming {
    .chat-message__bubble {
      border-color: $color-primary-light;
    }
  }
}

// 头像
.chat-message__avatar {
  flex-shrink: 0;
  padding-top: $spacing-xs;

  &--user {
    :deep(.el-avatar) {
      background-color: $color-primary;
      color: $color-white;
    }
  }

  &--assistant {
    :deep(.el-avatar) {
      background-color: $color-gray-200;
      color: $color-primary;
    }
  }
}

// 消息主体
.chat-message__body {
  flex: 1;
  min-width: 0;
  max-width: 70%;
}

// 发送者行
.chat-message__sender {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  margin-bottom: 4px;
}

.chat-message__sender-name {
  font-size: $font-size-sm;
  font-weight: $font-weight-medium;
  color: $color-gray-600;
}

.chat-message__time {
  font-size: $font-size-xs;
  color: $color-text-placeholder;
}

// 消息气泡
.chat-message__bubble {
  padding: $spacing-sm $spacing-base;
  word-break: break-word;
  overflow-wrap: break-word;
  position: relative;
  transition: border-color $transition-duration-fast $transition-ease;
}

// 纯文本消息
.chat-message__text {
  font-size: $font-size-base;
  line-height: $line-height-relaxed;
  white-space: pre-wrap;
}

// Markdown 内容
.chat-message__markdown {
  font-size: $font-size-base;
  line-height: $line-height-relaxed;

  // Override code blocks for dark background when inside user bubble (blue)
  :deep(pre) {
    background-color: #1e1e2d;
    border: 1px solid #2d2d3f;
    color: #e0e0e0;

    code {
      color: #e0e0e0;
    }
  }

  :deep(code) {
    background-color: rgba(0, 0, 0, 0.08);
    padding: 2px 6px;
    border-radius: $radius-sm;
    font-family: $font-family-mono;
    font-size: 0.9em;
  }

  :deep(p) {
    margin-bottom: $spacing-sm;

    &:last-child {
      margin-bottom: 0;
    }
  }

  :deep(ul),
  :deep(ol) {
    padding-left: $spacing-xl;
    margin-bottom: $spacing-sm;
  }

  :deep(blockquote) {
    border-left: 3px solid $color-gray-300;
    padding: $spacing-xs $spacing-base;
    margin: $spacing-sm 0;
    background-color: rgba(0, 0, 0, 0.03);
    border-radius: 0 $radius-sm $radius-sm 0;
  }

  :deep(table) {
    width: 100%;
    border-collapse: collapse;
    margin: $spacing-sm 0;
    font-size: $font-size-sm;

    th,
    td {
      padding: $spacing-xs $spacing-sm;
      border: 1px solid $color-gray-200;
      text-align: left;
    }

    th {
      background-color: $color-gray-100;
      font-weight: $font-weight-semibold;
    }
  }
}

// 流式输出光标动画
.chat-message__cursor {
  display: inline-block;
  width: 2px;
  height: 1.1em;
  background-color: $color-primary;
  margin-left: 1px;
  vertical-align: text-bottom;
  animation: cursor-blink 0.8s infinite;
}

// 消息出现动画
@keyframes message-appear {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

// 光标闪烁动画
@keyframes cursor-blink {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0;
  }
}

// 响应式
@media (max-width: $breakpoint-md) {
  .chat-message__body {
    max-width: 85%;
  }
}
</style>

<template>
  <div class="streaming-text" :class="{ 'streaming-text--active': isStreaming }">
    <div
      ref="contentRef"
      class="streaming-text__content markdown-content"
      v-html="renderedHtml"
    ></div>

    <!-- 流式输出光标 -->
    <span v-if="isStreaming" class="streaming-text__cursor">|</span>

    <!-- 空状态 -->
    <div v-if="!text && !isStreaming" class="streaming-text__empty">
      <span class="streaming-text__empty-text">等待 AI 响应...</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { marked } from 'marked'

// Configure marked for safe rendering
marked.setOptions({
  breaks: true,
  gfm: true,
})

interface Props {
  text: string
  isStreaming: boolean
}

const props = withDefaults(defineProps<Props>(), {
  text: '',
  isStreaming: false,
})

const contentRef = ref<HTMLElement | null>(null)

/** Render markdown to HTML safely */
const renderedHtml = computed(() => {
  if (!props.text) return ''
  try {
    return marked.parse(props.text) as string
  } catch {
    return `<p>${props.text}</p>`
  }
})

/** Auto-scroll to bottom when content updates */
watch(
  () => props.text,
  async () => {
    await nextTick()
    scrollToBottom()
  }
)

function scrollToBottom() {
  if (contentRef.value) {
    contentRef.value.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }
}

onMounted(() => {
  scrollToBottom()
})
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.streaming-text {
  position: relative;
  min-height: 60px;

  &--active {
    .streaming-text__content {
      // Subtle border hint while streaming
      border-right: none;
    }
  }
}

// 内容区域
.streaming-text__content {
  font-size: $font-size-base;
  line-height: $line-height-relaxed;
  color: $color-text-primary;
  word-break: break-word;
  overflow-wrap: break-word;

  // Fade-in animation for completed text
  animation: fade-in 0.5s $transition-ease-out;

  // Paragraph styles
  :deep(p) {
    margin-bottom: $spacing-md;

    &:last-child {
      margin-bottom: 0;
    }
  }

  // Heading styles
  :deep(h1),
  :deep(h2),
  :deep(h3),
  :deep(h4),
  :deep(h5),
  :deep(h6) {
    margin-top: $spacing-lg;
    margin-bottom: $spacing-sm;
    color: $color-gray-700;
    font-weight: $font-weight-semibold;

    &:first-child {
      margin-top: 0;
    }
  }

  :deep(h1) { font-size: $font-size-3xl; }
  :deep(h2) { font-size: $font-size-2xl; }
  :deep(h3) { font-size: $font-size-xl; }
  :deep(h4) { font-size: $font-size-lg; }
  :deep(h5) { font-size: $font-size-base; }
  :deep(h6) { font-size: $font-size-sm; }

  // Code blocks - dark background with syntax-highlighting styling
  :deep(pre) {
    background-color: #1e1e2d;
    border: 1px solid #2d2d3f;
    border-radius: $radius-lg;
    padding: $spacing-lg;
    overflow-x: auto;
    font-family: $font-family-mono;
    font-size: $font-size-sm;
    line-height: 1.6;
    color: #e0e0e0;
    margin: $spacing-md 0;
    white-space: pre;
    tab-size: 2;

    code {
      background: transparent;
      padding: 0;
      border: none;
      font-size: inherit;
      color: inherit;
    }
  }

  // Inline code
  :deep(code) {
    background-color: rgba(175, 184, 193, 0.2);
    padding: 2px 6px;
    border-radius: $radius-sm;
    font-family: $font-family-mono;
    font-size: 0.9em;
    color: $color-danger;
  }

  // Lists
  :deep(ul),
  :deep(ol) {
    padding-left: $spacing-2xl;
    margin-bottom: $spacing-md;

    li {
      margin-bottom: $spacing-xs;
    }

    ul, ol {
      margin-bottom: 0;
    }
  }

  :deep(ul) {
    list-style: disc;
  }

  :deep(ol) {
    list-style: decimal;
  }

  // Blockquote
  :deep(blockquote) {
    border-left: 4px solid $color-primary;
    padding: $spacing-sm $spacing-base;
    margin: $spacing-md 0;
    background-color: $color-primary-bg;
    border-radius: 0 $radius-md $radius-md 0;
    color: $color-gray-600;

    p:last-child {
      margin-bottom: 0;
    }
  }

  // Tables
  :deep(table) {
    width: 100%;
    margin: $spacing-md 0;
    border-collapse: collapse;
    border: 1px solid $color-gray-200;
    border-radius: $radius-md;
    overflow: hidden;

    th,
    td {
      padding: $spacing-sm $spacing-base;
      border: 1px solid $color-gray-200;
      text-align: left;
    }

    th {
      background-color: $color-gray-50;
      font-weight: $font-weight-semibold;
      color: $color-gray-600;
      font-size: $font-size-sm;
    }

    td {
      font-size: $font-size-sm;
      color: $color-text-regular;
    }

    tr:nth-child(even) td {
      background-color: $color-gray-50;
    }
  }

  // Horizontal rule
  :deep(hr) {
    border: none;
    border-top: 1px solid $color-gray-200;
    margin: $spacing-xl 0;
  }

  // Links
  :deep(a) {
    color: $color-primary;
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }

  // Images
  :deep(img) {
    max-width: 100%;
    border-radius: $radius-md;
    margin: $spacing-md 0;
  }

  // Strong and emphasis
  :deep(strong) {
    font-weight: $font-weight-semibold;
    color: $color-gray-700;
  }

  :deep(em) {
    font-style: italic;
  }
}

// 流式输出光标动画
.streaming-text__cursor {
  display: inline-block;
  color: $color-primary;
  font-weight: $font-weight-bold;
  font-size: $font-size-lg;
  line-height: 1;
  margin-left: 2px;
  animation: cursor-blink 0.8s infinite;
  vertical-align: text-bottom;
}

// 空状态
.streaming-text__empty {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding: $spacing-base 0;
}

.streaming-text__empty-text {
  font-size: $font-size-base;
  color: $color-text-placeholder;
}

// 光标闪烁
@keyframes cursor-blink {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0;
  }
}

// 内容渐入
@keyframes fade-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>

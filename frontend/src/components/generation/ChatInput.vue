<template>
  <div class="chat-input" :class="{ 'chat-input--disabled': disabled }">
    <div class="chat-input__wrapper">
      <el-input
        ref="inputRef"
        v-model="inputText"
        type="textarea"
        :rows="2"
        :autosize="{ minRows: 2, maxRows: 6 }"
        :placeholder="placeholder"
        :disabled="disabled"
        :maxlength="2000"
        show-word-limit
        resize="none"
        class="chat-input__textarea"
        @keydown.enter.exact="handleEnterKey"
        @keydown.ctrl.enter="handleSend"
      >
        <template #suffix>
          <span class="chat-input__hint">Ctrl+Enter 发送</span>
        </template>
      </el-input>

      <div class="chat-input__actions">
        <span class="chat-input__count">
          {{ inputText.length }} / 2000
        </span>
        <el-button
          type="primary"
          :icon="Promotion"
          :disabled="disabled || !inputText.trim()"
          :loading="disabled"
          @click="handleSend"
        >
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { Promotion } from '@element-plus/icons-vue'

interface Props {
  disabled?: boolean
  placeholder?: string
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  placeholder: '请输入您的问题或需求...',
})

interface Emits {
  (e: 'send', message: string): void
}

const emit = defineEmits<Emits>()

const inputRef = ref<InstanceType<typeof HTMLTextAreaElement> | null>(null)
const inputText = ref('')

/** Handle Enter key: Enter alone with no shift sends, Ctrl+Enter always sends */
function handleEnterKey(event: KeyboardEvent) {
  // If only Enter pressed (not Shift+Enter, not Ctrl+Enter), send
  if (!event.shiftKey && !event.ctrlKey) {
    event.preventDefault()
    handleSend()
  }
}

/** Emit send event and clear input */
function handleSend() {
  const trimmed = inputText.value.trim()
  if (!trimmed || props.disabled) return

  emit('send', trimmed)
  inputText.value = ''

  nextTick(() => {
    inputRef.value?.focus()
  })
}
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.chat-input {
  width: 100%;
  padding: $spacing-base;
  background-color: $color-white;
  border-top: 1px solid $color-gray-200;

  &--disabled {
    opacity: 0.6;
    pointer-events: none;
  }
}

.chat-input__wrapper {
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
}

.chat-input__textarea {
  :deep(.el-textarea__inner) {
    border-radius: $radius-lg;
    font-size: $font-size-base;
    line-height: $line-height-relaxed;
    padding: $spacing-sm $spacing-base;
    background-color: $color-gray-50;
    border-color: $color-gray-200;
    transition: all $transition-duration-fast $transition-ease;

    &:hover {
      border-color: $color-primary-light;
      background-color: $color-white;
    }

    &:focus {
      border-color: $color-primary;
      background-color: $color-white;
      box-shadow: 0 0 0 2px $color-primary-bg;
    }

    &:disabled {
      background-color: $color-gray-100;
      color: $color-text-disabled;
      cursor: not-allowed;
    }

    &::placeholder {
      color: $color-text-placeholder;
    }
  }

  :deep(.el-input__count) {
    bottom: 2px;
    right: 8px;
    font-size: $font-size-xs;
    color: $color-text-placeholder;
  }
}

.chat-input__hint {
  display: block;
  padding: 0 $spacing-xs;
  font-size: $font-size-xs;
  color: $color-text-placeholder;
  white-space: nowrap;
}

.chat-input__actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: $spacing-base;
}

.chat-input__count {
  font-size: $font-size-xs;
  color: $color-text-placeholder;
  white-space: nowrap;
}
</style>

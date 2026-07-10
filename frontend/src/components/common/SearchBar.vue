<template>
  <div class="search-bar">
    <el-input
      v-model="innerValue"
      :placeholder="placeholder"
      :clearable="clearable"
      :disabled="disabled"
      :size="size"
      class="search-input"
      @keyup.enter="handleEnter"
      @clear="handleClear"
    >
      <!-- 搜索图标前缀 -->
      <template #prefix>
        <el-icon><Search /></el-icon>
      </template>
      <!-- 搜索按钮后缀 -->
      <template #suffix>
        <el-button
          :size="size"
          type="primary"
          :disabled="disabled"
          class="search-button"
          @click="triggerSearch"
        >
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
      </template>
    </el-input>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onBeforeUnmount } from 'vue'
import { Search } from '@element-plus/icons-vue'

// -------------------------------------------------------------------
// Props
// -------------------------------------------------------------------
const props = withDefaults(
  defineProps<{
    /** v-model 绑定的值 */
    modelValue?: string
    /** 占位文本 */
    placeholder?: string
    /** 防抖时间（毫秒） */
    debounceTime?: number
    /** 是否可清空 */
    clearable?: boolean
    /** 是否禁用 */
    disabled?: boolean
    /** 尺寸 */
    size?: 'large' | 'default' | 'small'
  }>(),
  {
    modelValue: '',
    placeholder: '请输入关键词搜索',
    debounceTime: 300,
    clearable: true,
    disabled: false,
    size: 'default',
  },
)

// -------------------------------------------------------------------
// Emits
// -------------------------------------------------------------------
const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'search', value: string): void
  (e: 'clear'): void
}>()

// -------------------------------------------------------------------
// 内部状态
// -------------------------------------------------------------------
const innerValue = ref<string>(props.modelValue)

// 防抖定时器
let debounceTimer: ReturnType<typeof setTimeout> | null = null

// -------------------------------------------------------------------
// 监听外部 modelValue 变化
// -------------------------------------------------------------------
watch(
  () => props.modelValue,
  (val) => {
    innerValue.value = val
  },
)

// -------------------------------------------------------------------
// 监听内部值变化，同步 v-model 并触发防抖搜索
// -------------------------------------------------------------------
watch(innerValue, (val) => {
  emit('update:modelValue', val)
  debounceEmitSearch(val)
})

// -------------------------------------------------------------------
// 防抖触发搜索
// -------------------------------------------------------------------
function debounceEmitSearch(value: string) {
  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }
  debounceTimer = setTimeout(() => {
    emit('search', value)
  }, props.debounceTime)
}

// -------------------------------------------------------------------
// 立即触发搜索（回车 / 点击按钮）
// -------------------------------------------------------------------
function triggerSearch() {
  // 取消防抖定时器，立即触发
  if (debounceTimer) {
    clearTimeout(debounceTimer)
    debounceTimer = null
  }
  emit('search', innerValue.value)
}

// -------------------------------------------------------------------
// 回车事件
// -------------------------------------------------------------------
function handleEnter() {
  triggerSearch()
}

// -------------------------------------------------------------------
// 清空事件
// -------------------------------------------------------------------
function handleClear() {
  emit('clear')
  // 清空后也触发展示全部数据
  emit('search', '')
}

// -------------------------------------------------------------------
// 组件卸载时清理定时器
// -------------------------------------------------------------------
onBeforeUnmount(() => {
  if (debounceTimer) {
    clearTimeout(debounceTimer)
    debounceTimer = null
  }
})
</script>

<style scoped lang="scss">
.search-bar {
  display: inline-flex;
  align-items: center;

  .search-input {
    width: 320px;

    :deep(.el-input__prefix) {
      color: #909399;
      font-size: 16px;
      left: 12px;
    }

    :deep(.el-input__inner) {
      padding-right: 90px; // 为搜索按钮留出空间
      border-radius: 6px;
    }

    :deep(.el-input__suffix) {
      right: 2px;
      display: flex;
      align-items: center;
    }
  }

  .search-button {
    border-radius: 0 5px 5px 0;
    margin-right: -1px;
    font-size: 13px;

    .el-icon {
      margin-right: 4px;
      font-size: 14px;
    }
  }
}
</style>

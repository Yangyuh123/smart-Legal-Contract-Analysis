<template>
  <el-dialog
    v-model="dialogVisible"
    :title="title"
    width="420px"
    :close-on-click-modal="closeOnClickModal"
    :close-on-press-escape="closeOnPressEscape"
    :destroy-on-close="destroyOnClose"
    :append-to-body="appendToBody"
    class="confirm-dialog"
    @close="handleCancel"
  >
    <!-- 内容区域 -->
    <div class="confirm-body">
      <div class="confirm-icon" :class="`confirm-icon--${type}`">
        <el-icon :size="24">
          <WarningFilled v-if="type === 'warning'" />
          <CircleCloseFilled v-else-if="type === 'danger'" />
          <InfoFilled v-else />
        </el-icon>
      </div>

      <p class="confirm-message" v-html="formattedMessage" />
    </div>

    <!-- 底部按钮 -->
    <template #footer>
      <div class="confirm-footer">
        <el-button :disabled="loading" @click="handleCancel">
          {{ cancelText }}
        </el-button>
        <el-button
          :type="confirmButtonType"
          :loading="loading"
          @click="handleConfirm"
        >
          {{ confirmText }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { WarningFilled, CircleCloseFilled, InfoFilled } from '@element-plus/icons-vue'

// -------------------------------------------------------------------
// Props
// -------------------------------------------------------------------
const props = withDefaults(
  defineProps<{
    /** 是否显示对话框 */
    visible?: boolean
    /** 标题 */
    title?: string
    /** 消息文本（支持换行符 \n） */
    message?: string
    /** 确认按钮文本 */
    confirmText?: string
    /** 取消按钮文本 */
    cancelText?: string
    /** 对话框类型（决定图标和按钮颜色） */
    type?: 'warning' | 'danger' | 'info'
    /** 确认按钮是否显示加载状态 */
    loading?: boolean
    /** 是否可通过点击遮罩关闭 */
    closeOnClickModal?: boolean
    /** 是否可通过 Esc 关闭 */
    closeOnPressEscape?: boolean
    /** 关闭时销毁组件 */
    destroyOnClose?: boolean
    /** 是否使用 Teleport 挂载到 body */
    appendToBody?: boolean
  }>(),
  {
    visible: false,
    title: '确认操作',
    message: '',
    confirmText: '确定',
    cancelText: '取消',
    type: 'warning',
    loading: false,
    closeOnClickModal: false,
    closeOnPressEscape: true,
    destroyOnClose: true,
    appendToBody: true,
  },
)

// -------------------------------------------------------------------
// Emits
// -------------------------------------------------------------------
const emit = defineEmits<{
  (e: 'confirm'): void
  (e: 'cancel'): void
  (e: 'update:visible', value: boolean): void
}>()

// -------------------------------------------------------------------
// 内部状态
// -------------------------------------------------------------------
const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val),
})

// -------------------------------------------------------------------
// 计算属性
// -------------------------------------------------------------------

/** 确认按钮类型（与 Element Plus button type 对应） */
const confirmButtonType = computed(() => {
  switch (props.type) {
    case 'danger':
      return 'danger'
    case 'warning':
      return 'warning'
    case 'info':
    default:
      return 'primary'
  }
})

/** 格式化消息（支持 \n 换行） */
const formattedMessage = computed(() => {
  if (!props.message) return ''
  return props.message.replace(/\n/g, '<br />')
})

// -------------------------------------------------------------------
// 事件处理
// -------------------------------------------------------------------
function handleConfirm() {
  emit('confirm')
}

function handleCancel() {
  emit('cancel')
  dialogVisible.value = false
}
</script>

<style scoped lang="scss">
.confirm-dialog {
  :deep(.el-dialog__header) {
    padding: 20px 24px 16px;
    margin-right: 0;
    border-bottom: 1px solid #ebeef5;

    .el-dialog__title {
      font-size: 16px;
      font-weight: 600;
      color: #303133;
    }
  }

  :deep(.el-dialog__body) {
    padding: 24px;
  }

  :deep(.el-dialog__footer) {
    padding: 12px 24px 20px;
  }
}

// ---- 内容区 ----
.confirm-body {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

// ---- 图标 ----
.confirm-icon {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;

  &--warning {
    background-color: rgba(229, 165, 10, 0.1);
    color: #e5a50a;
  }

  &--danger {
    background-color: rgba(192, 28, 40, 0.1);
    color: #c01c28;
  }

  &--info {
    background-color: rgba(53, 132, 228, 0.1);
    color: #3584e4;
  }
}

// ---- 消息 ----
.confirm-message {
  margin: 0;
  font-size: 14px;
  color: #606266;
  line-height: 1.7;
  word-break: break-word;
  flex: 1;
  padding-top: 10px; // 与图标垂直居中
}

// ---- 底部按钮 ----
.confirm-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>

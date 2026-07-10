<template>
  <div class="file-upload">
    <el-upload
      ref="uploadRef"
      class="upload-zone"
      drag
      :accept="accept"
      :multiple="multiple"
      :disabled="disabled"
      :auto-upload="false"
      :show-file-list="false"
      :http-request="noopHttpRequest"
      :before-upload="handleBeforeUpload"
      @change="handleFileChange"
    >
      <!-- 拖拽区域内容 -->
      <div class="upload-content" :class="{ 'is-disabled': disabled }">
        <!-- 上传图标 -->
        <div class="upload-icon-wrapper">
          <el-icon class="upload-icon"><UploadFilled /></el-icon>
        </div>

        <!-- 主提示文本 -->
        <div class="upload-primary-text">
          将文件拖到此处，或<span class="upload-link">点击上传</span>
        </div>

        <!-- 副文本：支持的文件格式 -->
        <div class="upload-secondary-text">
          {{ formattedAcceptText }}
        </div>

        <!-- 自定义提示 -->
        <div v-if="tip" class="upload-tip">
          <el-icon class="tip-icon"><InfoFilled /></el-icon>
          {{ tip }}
        </div>
      </div>
    </el-upload>

    <!-- 已选文件列表 -->
    <TransitionGroup name="file-list" tag="div" class="file-list" v-if="fileList.length > 0">
      <div
        v-for="(file, index) in fileList"
        :key="file.uid || file.name + file.size"
        class="file-item"
      >
        <!-- 文件图标 -->
        <div class="file-icon">
          <el-icon :size="24"><Document /></el-icon>
        </div>

        <!-- 文件信息 -->
        <div class="file-info">
          <span class="file-name" :title="file.name">{{ file.name }}</span>
          <span class="file-size">{{ formatFileSize(file.size) }}</span>
        </div>

        <!-- 上传进度 -->
        <div v-if="uploading" class="file-progress">
          <el-progress :percentage="progress" :stroke-width="6" :show-text="false" />
        </div>

        <!-- 成功图标 -->
        <el-icon v-else class="file-success-icon" color="#26a269"><CircleCheckFilled /></el-icon>

        <!-- 移除按钮 -->
        <el-button
          class="file-remove-btn"
          :disabled="disabled"
          type="danger"
          link
          @click="handleRemoveFile(index)"
        >
          <el-icon><Delete /></el-icon>
        </el-button>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, Document, Delete, CircleCheckFilled, InfoFilled } from '@element-plus/icons-vue'
import type { UploadProps, UploadFile, UploadInstance } from 'element-plus'

// -------------------------------------------------------------------
// Props
// -------------------------------------------------------------------
const props = withDefaults(
  defineProps<{
    /** 允许上传的文件类型（MIME 或扩展名，如 ".pdf,.doc,.docx,.txt"） */
    accept?: string
    /** 最大文件大小（MB） */
    maxSize?: number
    /** 是否禁用 */
    disabled?: boolean
    /** 是否允许多个文件 */
    multiple?: boolean
    /** 自定义提示文本 */
    tip?: string
  }>(),
  {
    accept: '.pdf,.doc,.docx,.txt',
    maxSize: 50,
    disabled: false,
    multiple: false,
    tip: '',
  },
)

// -------------------------------------------------------------------
// Emits
// -------------------------------------------------------------------
const emit = defineEmits<{
  (e: 'file-selected', file: File): void
  (e: 'file-removed', index: number): void
  (e: 'update:fileList', fileList: File[]): void
}>()

// -------------------------------------------------------------------
// 状态
// -------------------------------------------------------------------
const uploadRef = ref<UploadInstance>()
const fileList = ref<File[]>([])
const progress = ref<number>(0)
const uploading = ref<boolean>(false)

// -------------------------------------------------------------------
// 计算属性
// -------------------------------------------------------------------

/** 格式化的接受类型文本 */
const formattedAcceptText = computed(() => {
  if (!props.accept) return ''
  const extensions = props.accept
    .split(',')
    .map((ext) => ext.trim().toUpperCase().replace('.', ''))
  return `支持 ${extensions.join('、')} 格式，单个文件不超过 ${props.maxSize}MB`
})

// -------------------------------------------------------------------
// 工具函数
// -------------------------------------------------------------------

/** 格式化文件大小 */
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/** 从文件名获取扩展名 */
function getFileExtension(filename: string): string {
  const parts = filename.split('.')
  return parts.length > 1 ? `.${parts[parts.length - 1].toLowerCase()}` : ''
}

// -------------------------------------------------------------------
// 无效的 HTTP 请求方法（auto-upload 为 false，但仍需提供）
// -------------------------------------------------------------------
function noopHttpRequest() {
  // 不实际执行上传
}

// -------------------------------------------------------------------
// 上传前验证
// -------------------------------------------------------------------
const handleBeforeUpload: UploadProps['beforeUpload'] = (rawFile: File) => {
  // 1. 文件类型校验
  if (props.accept) {
    const allowedExtensions = props.accept
      .split(',')
      .map((ext) => ext.trim().toLowerCase())
    const fileExt = getFileExtension(rawFile.name)

    // 检查扩展名
    const isExtAllowed = allowedExtensions.some((allowed) => {
      if (allowed.startsWith('.')) {
        return fileExt === allowed
      }
      // MIME 类型匹配
      return rawFile.type === allowed
    })

    if (!isExtAllowed) {
      const extList = props.accept.replace(/\./g, '').toUpperCase()
      ElMessage.warning(`不支持的文件格式，仅允许上传 ${extList} 格式文件`)
      return false
    }
  }

  // 2. 文件大小校验
  const maxSizeBytes = props.maxSize * 1024 * 1024
  if (rawFile.size > maxSizeBytes) {
    ElMessage.warning(`文件大小不能超过 ${props.maxSize}MB，当前文件大小为 ${formatFileSize(rawFile.size)}`)
    return false
  }

  return true
}

// -------------------------------------------------------------------
// 文件变更处理
// -------------------------------------------------------------------
function handleFileChange(uploadFile: UploadFile) {
  // auto-upload 为 false 时，file 对象在 raw 属性上
  const rawFile = uploadFile.raw
  if (!rawFile) return

  // 若非多选模式，清空之前的文件
  if (!props.multiple) {
    fileList.value = []
  }

  // 添加到文件列表
  fileList.value.push(rawFile)

  // 模拟上传进度
  simulateUpload()

  // 触发事件
  emit('file-selected', rawFile)
  emit('update:fileList', [...fileList.value])
}

// -------------------------------------------------------------------
// 模拟上传进度
// -------------------------------------------------------------------
async function simulateUpload() {
  uploading.value = true
  progress.value = 0

  // 模拟进度递增
  return new Promise<void>((resolve) => {
    const interval = setInterval(() => {
      if (progress.value >= 100) {
        clearInterval(interval)
        uploading.value = false
        resolve()
      } else {
        // 非匀速递增，模拟真实上传
        const step = Math.random() * 15 + 5
        progress.value = Math.min(progress.value + step, 100)
      }
    }, 200)
  })
}

// -------------------------------------------------------------------
// 移除文件
// -------------------------------------------------------------------
function handleRemoveFile(index: number) {
  if (props.disabled) return
  fileList.value.splice(index, 1)
  progress.value = 0
  uploading.value = false
  emit('file-removed', index)
  emit('update:fileList', [...fileList.value])
}

// -------------------------------------------------------------------
// 暴露方法
// -------------------------------------------------------------------
defineExpose({
  /** 清空文件列表 */
  clearFiles() {
    fileList.value = []
    progress.value = 0
    uploading.value = false
    uploadRef.value?.clearFiles()
  },
  /** 获取当前文件列表 */
  getFiles: () => fileList.value,
  /** 手动设置文件列表 */
  setFiles(files: File[]) {
    fileList.value = files
    emit('update:fileList', [...fileList.value])
  },
})
</script>

<style scoped lang="scss">
.file-upload {
  width: 100%;

  // ---- 上传区域 ----
  .upload-zone {
    width: 100%;

    :deep(.el-upload) {
      display: block;
      width: 100%;
    }

    :deep(.el-upload-dragger) {
      width: 100%;
      min-height: 180px;
      border: 2px dashed #dcdfe6;
      border-radius: 8px;
      background-color: #fafbfc;
      transition: border-color 0.3s cubic-bezier(0.4, 0, 0.2, 1),
        background-color 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 40px 24px;

      &:hover {
        border-color: #1a5fb4;
        background-color: rgba(26, 95, 180, 0.03);
      }

      &.is-dragover {
        border-color: #1a5fb4;
        background-color: rgba(26, 95, 180, 0.06);
      }
    }
  }

  // ---- 上传区域内容 ----
  .upload-content {
    text-align: center;

    &.is-disabled {
      opacity: 0.45;
      cursor: not-allowed;

      .upload-link {
        color: #c0c4cc;
      }
    }
  }

  .upload-icon-wrapper {
    margin-bottom: 12px;

    .upload-icon {
      font-size: 48px;
      color: #c0c4cc;
      transition: color 0.3s;

      .is-dragover & {
        color: #1a5fb4;
      }
    }
  }

  .upload-primary-text {
    font-size: 16px;
    color: #303133;
    margin-bottom: 8px;
    font-weight: 500;

    .upload-link {
      color: #1a5fb4;
      cursor: pointer;

      &:hover {
        color: #3584e4;
        text-decoration: underline;
      }
    }
  }

  .upload-secondary-text {
    font-size: 13px;
    color: #909399;
    line-height: 1.5;
  }

  .upload-tip {
    margin-top: 10px;
    font-size: 12px;
    color: #909399;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;

    .tip-icon {
      font-size: 14px;
    }
  }

  // ---- 文件列表 ----
  .file-list {
    margin-top: 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .file-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    background-color: #fafbfc;
    border: 1px solid #ebeef5;
    border-radius: 6px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

    &:hover {
      border-color: #dcdfe6;
      background-color: #f5f6fa;
    }
  }

  .file-icon {
    flex-shrink: 0;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: rgba(26, 95, 180, 0.08);
    border-radius: 6px;
    color: #1a5fb4;
  }

  .file-info {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .file-name {
    font-size: 14px;
    color: #303133;
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .file-size {
    font-size: 12px;
    color: #909399;
  }

  .file-progress {
    width: 100px;
    flex-shrink: 0;
  }

  .file-success-icon {
    font-size: 20px;
    flex-shrink: 0;
  }

  .file-remove-btn {
    flex-shrink: 0;
    font-size: 18px;
    padding: 4px;

    &:hover {
      background-color: rgba(192, 28, 40, 0.08);
      border-radius: 4px;
    }
  }

  // ---- 列表过渡动画 ----
  .file-list-enter-active,
  .file-list-leave-active {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .file-list-enter-from {
    opacity: 0;
    transform: translateY(-8px);
  }

  .file-list-leave-to {
    opacity: 0;
    transform: translateX(20px);
  }

  .file-list-leave-active {
    position: absolute;
  }
}
</style>

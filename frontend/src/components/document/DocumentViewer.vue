<template>
  <div class="document-viewer">
    <!-- 工具栏 -->
    <div class="viewer-toolbar">
      <div class="toolbar-left">
        <el-icon class="file-icon"><Document /></el-icon>
        <span class="file-name" :title="fileName">{{ fileName || '未命名文件' }}</span>
        <el-tag :type="fileTypeTagType" size="small" class="file-type-badge">
          {{ fileType.toUpperCase() }}
        </el-tag>
      </div>
      <div class="toolbar-right">
        <el-button
          v-if="fileUrl"
          type="primary"
          size="small"
          :icon="Download"
          @click="handleDownload"
        >
          下载
        </el-button>
      </div>
    </div>

    <!-- 文档内容区域 -->
    <div class="viewer-content">
      <!-- 无文件地址 -->
      <div v-if="!fileUrl" class="viewer-placeholder">
        <el-icon class="placeholder-icon"><WarningFilled /></el-icon>
        <p class="placeholder-text">暂无文件地址，无法预览文档</p>
      </div>

      <!-- 加载状态 -->
      <div v-else-if="loading" class="viewer-loading">
        <el-icon class="loading-icon is-loading"><Loading /></el-icon>
        <p class="loading-text">文档正在加载中，请稍候...</p>
        <el-progress :percentage="loadingProgress" :show-text="false" :stroke-width="4" />
      </div>

      <!-- 加载错误 -->
      <div v-else-if="loadError" class="viewer-error">
        <el-result
          icon="error"
          title="文档加载失败"
          :sub-title="errorMessage"
        >
          <template #extra>
            <el-button type="primary" @click="retryLoad">重新加载</el-button>
            <el-button v-if="fileUrl" @click="handleDownload">下载查看</el-button>
          </template>
        </el-result>
      </div>

      <!-- PDF 预览 -->
      <iframe
        v-else-if="fileType === 'pdf'"
        :src="pdfViewerUrl"
        class="viewer-iframe"
        frameborder="0"
        @load="onIframeLoad"
        @error="onIframeError"
      ></iframe>

      <!-- Office 文档预览 -->
      <iframe
        v-else
        :src="officeViewerUrl"
        class="viewer-iframe"
        frameborder="0"
        @load="onIframeLoad"
        @error="onIframeError"
      ></iframe>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { Document, Download, Loading, WarningFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

interface Props {
  fileUrl: string
  fileName: string
  fileType?: 'pdf' | 'docx' | 'doc'
}

const props = withDefaults(defineProps<Props>(), {
  fileType: 'pdf',
  fileName: '',
})

const loading = ref(true)
const loadingProgress = ref(0)
const loadError = ref(false)
const errorMessage = ref('')

let progressTimer: ReturnType<typeof setInterval> | null = null

/** PDF viewer URL */
const pdfViewerUrl = computed(() => {
  if (!props.fileUrl) return ''
  return props.fileUrl
})

/** Google Docs viewer URL for office documents */
const officeViewerUrl = computed(() => {
  if (!props.fileUrl) return ''
  const encodedUrl = encodeURIComponent(props.fileUrl)
  return `https://docs.google.com/viewer?url=${encodedUrl}&embedded=true`
})

/** Tag type based on file type */
const fileTypeTagType = computed(() => {
  switch (props.fileType) {
    case 'pdf':
      return 'danger'
    case 'docx':
      return 'primary'
    case 'doc':
      return 'info'
    default:
      return 'info'
  }
})

/** Start simulated loading progress */
function startLoading() {
  loading.value = true
  loadError.value = false
  errorMessage.value = ''
  loadingProgress.value = 0

  if (progressTimer) clearInterval(progressTimer)

  progressTimer = setInterval(() => {
    if (loadingProgress.value < 90) {
      loadingProgress.value += Math.random() * 15 + 2
      if (loadingProgress.value > 90) loadingProgress.value = 90
    }
  }, 400)
}

/** Stop loading progress */
function stopLoading(success: boolean = true) {
  if (progressTimer) {
    clearInterval(progressTimer)
    progressTimer = null
  }

  if (success) {
    loadingProgress.value = 100
    setTimeout(() => {
      loading.value = false
    }, 300)
  }
}

/** Handle iframe load success */
function onIframeLoad() {
  stopLoading(true)
}

/** Handle iframe load error */
function onIframeError() {
  stopLoading(false)
  loadError.value = true
  errorMessage.value = '无法加载文档，请检查网络连接或文件地址是否正确'
}

/** Retry loading */
function retryLoad() {
  startLoading()
  const container = document.querySelector('.viewer-content') as HTMLElement
  if (container) {
    const iframes = container.querySelectorAll('iframe')
    iframes.forEach((iframe) => {
      const src = iframe.src
      iframe.src = ''
      setTimeout(() => {
        iframe.src = src
      }, 50)
    })
  }
}

/** Download the document */
function handleDownload() {
  if (!props.fileUrl) {
    ElMessage.warning('文件地址为空，无法下载')
    return
  }
  const link = document.createElement('a')
  link.href = props.fileUrl
  link.download = props.fileName || 'document'
  link.target = '_blank'
  link.rel = 'noopener noreferrer'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// Watch fileUrl changes
watch(
  () => props.fileUrl,
  (newUrl) => {
    if (newUrl) {
      startLoading()
    } else {
      loading.value = false
      loadError.value = false
    }
  }
)

onMounted(() => {
  if (props.fileUrl) {
    startLoading()
  } else {
    loading.value = false
  }
})

onBeforeUnmount(() => {
  if (progressTimer) {
    clearInterval(progressTimer)
    progressTimer = null
  }
})
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.document-viewer {
  width: 100%;
  min-height: 600px;
  display: flex;
  flex-direction: column;
  border: 1px solid $color-gray-200;
  border-radius: $radius-lg;
  overflow: hidden;
  background-color: $color-white;
}

// 工具栏
.viewer-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $spacing-sm $spacing-base;
  background-color: $color-gray-50;
  border-bottom: 1px solid $color-gray-200;
  min-height: 44px;
  flex-shrink: 0;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  min-width: 0;
  flex: 1;
}

.file-icon {
  font-size: $font-size-xl;
  color: $color-danger;
  flex-shrink: 0;
}

.file-name {
  font-size: $font-size-base;
  font-weight: $font-weight-medium;
  color: $color-gray-700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 300px;
}

.file-type-badge {
  flex-shrink: 0;
  text-transform: uppercase;
  font-weight: $font-weight-semibold;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  flex-shrink: 0;
}

// 内容区域
.viewer-content {
  flex: 1;
  position: relative;
  min-height: 560px;
  background-color: #f0f0f0;
}

// 内嵌文档
.viewer-iframe {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: none;
}

// 占位状态
.viewer-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 560px;
  color: $color-text-secondary;
  gap: $spacing-base;
}

.placeholder-icon {
  font-size: 48px;
  color: $color-gray-400;
}

.placeholder-text {
  font-size: $font-size-base;
  color: $color-text-placeholder;
  margin: 0;
}

// 加载状态
.viewer-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 560px;
  gap: $spacing-base;
  padding: $spacing-3xl;
}

.loading-icon {
  font-size: 36px;
  color: $color-primary;
}

.loading-text {
  font-size: $font-size-base;
  color: $color-text-secondary;
  margin: 0;
}

:deep(.el-progress) {
  width: 300px;
  max-width: 80%;
}

// 错误状态
.viewer-error {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 560px;
}

// 响应式
@media (max-width: $breakpoint-md) {
  .document-viewer {
    min-height: 400px;
  }

  .viewer-content {
    min-height: 360px;
  }

  .viewer-placeholder,
  .viewer-loading,
  .viewer-error {
    min-height: 360px;
  }

  .file-name {
    max-width: 160px;
  }
}
</style>

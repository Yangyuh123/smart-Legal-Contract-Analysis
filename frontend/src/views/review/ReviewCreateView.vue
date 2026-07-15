<template>
  <div class="review-page sl-page">
    <div class="sl-page-title">智能审查</div>
    <div class="sl-page-subtitle">上传合同文件，AI 自动识别法律风险并给出修改建议</div>

    <n-card :bordered="false" class="review-card">
      <div v-if="!file">
        <n-upload
          :default-upload="false"
          :max="1"
          accept=".pdf,.docx,.doc"
          @change="handleChange"
        >
          <n-upload-dragger>
            <div style="margin-bottom: 10px;">
              <n-icon :size="46" :depth="3"><CloudUploadOutline /></n-icon>
            </div>
            <n-text style="font-size: 16px;">将合同文件拖到此处，或点击上传</n-text>
            <n-p depth="3" style="margin: 8px 0 0;">支持 PDF、DOCX、DOC，最大 50MB</n-p>
          </n-upload-dragger>
        </n-upload>
      </div>

      <div v-else>
        <div class="file-card">
          <n-icon :size="42" color="#6366f1"><DocumentTextOutline /></n-icon>
          <div class="file-info">
            <strong>{{ file.name }}</strong>
            <span>{{ (file.size / 1024 / 1024).toFixed(1) }} MB</span>
          </div>
          <n-button circle size="small" @click="file = null">
            <template #icon><n-icon :component="CloseOutline" /></template>
          </n-button>
        </div>

        <n-input
          v-model:value="reviewScope"
          type="textarea"
          :rows="2"
          placeholder="审查重点（可选）"
          style="margin-top: 16px;"
        />
        <n-button
          type="primary"
          size="large"
          block
          :loading="submitting"
          style="margin-top: 12px;"
          @click="handleSubmit"
        >
          {{ submitting ? '审查中，请稍候...' : '开始智能审查' }}
        </n-button>
      </div>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage, type UploadFileInfo } from 'naive-ui'
import { CloudUploadOutline, DocumentTextOutline, CloseOutline } from '@vicons/ionicons5'

const router = useRouter()
const message = useMessage()
const file = ref<File | null>(null)
const reviewScope = ref('')
const submitting = ref(false)

function handleChange(data: { fileList: UploadFileInfo[] }) {
  const last = data.fileList[data.fileList.length - 1]
  const raw = (last?.file as File) || null
  if (raw && (!/\.(pdf|docx|doc)$/i.test(raw.name) || raw.size > 50 * 1024 * 1024)) {
    message.error('仅支持 PDF/DOCX/DOC，最大 50MB')
    return
  }
  file.value = raw
}

async function handleSubmit() {
  if (!file.value) return
  submitting.value = true
  try {
    const fd = new FormData()
    fd.append('file', file.value)
    if (reviewScope.value) fd.append('reviewScope', reviewScope.value)
    const token = localStorage.getItem('access_token')
    const resp = await fetch('/api/v1/reviews/upload', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: fd,
    })
    const data = await resp.json()
    if (data.code === 200) {
      message.success('审查完成')
      router.push(`/review/${data.data.id}`)
    } else {
      message.error(data.message || '审查失败')
    }
  } catch (e: any) {
    message.error('请求失败: ' + e.message)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.review-card {
  max-width: 600px;
  margin-top: 20px;
}
.file-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border: 2px solid var(--sl-primary);
  border-radius: 12px;
  background: var(--sl-primary-soft);
}
.file-info {
  flex: 1;
}
.file-info strong {
  display: block;
  font-size: 15px;
  color: var(--sl-text-1);
}
.file-info span {
  font-size: 13px;
  color: var(--sl-text-3);
}
</style>

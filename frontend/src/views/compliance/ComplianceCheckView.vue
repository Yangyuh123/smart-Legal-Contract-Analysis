<template>
  <div class="compliance-page sl-page">
    <div class="sl-page-title">合规检查</div>
    <div class="sl-page-subtitle">上传合同文件，AI 自动检查合规性并给出整改建议</div>

    <n-card :bordered="false" class="compliance-card">
      <!-- 文件上传区域 -->
      <div v-if="!file">
        <n-upload
          :default-upload="false"
          :max="1"
          accept=".pdf,.docx,.doc"
          @change="handleChange"
        >
          <n-upload-dragger>
            <div style="margin-bottom: 10px;">
              <n-icon :size="46" :depth="3"><ShieldCheckmarkOutline /></n-icon>
            </div>
            <n-text style="font-size: 16px;">将合同文件拖到此处，或点击上传</n-text>
            <n-p depth="3" style="margin: 8px 0 0;">支持 PDF、DOCX、DOC，最大 50MB</n-p>
          </n-upload-dragger>
        </n-upload>
      </div>

      <!-- 文件已选择区域 -->
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

        <!-- 合规标准选择 -->
        <n-select
          v-model:value="complianceStandard"
          :options="standardOptions"
          placeholder="请选择合规标准"
          style="margin-top: 16px;"
        />

        <!-- 行业领域输入 -->
        <n-input
          v-model:value="industry"
          placeholder="行业领域（可选）"
          style="margin-top: 12px;"
        />

        <!-- 司法管辖区输入 -->
        <n-input
          v-model:value="jurisdiction"
          placeholder="司法管辖区（可选，默认中国大陆）"
          style="margin-top: 12px;"
        />

        <!-- 开始检查按钮 -->
        <n-button
          type="primary"
          size="large"
          block
          :loading="submitting"
          :disabled="!complianceStandard"
          style="margin-top: 16px;"
          @click="handleSubmit"
        >
          {{ submitting ? '检查中，请稍候...' : '开始合规检查' }}
        </n-button>
      </div>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage, type UploadFileInfo } from 'naive-ui'
import { ShieldCheckmarkOutline, DocumentTextOutline, CloseOutline } from '@vicons/ionicons5'
import { complianceApi } from '@/api/compliance'

const router = useRouter()
const message = useMessage()
const file = ref<File | null>(null)
const complianceStandard = ref('')
const industry = ref('')
const jurisdiction = ref('')
const submitting = ref(false)

const standardOptions = [
  { label: '数据安全法', value: '数据安全法' },
  { label: '个人信息保护法', value: '个人信息保护法' },
  { label: 'GDPR（欧盟通用数据保护条例）', value: 'GDPR' },
  { label: '消费者权益保护法', value: '消费者权益保护法' },
  { label: '网络安全法', value: '网络安全法' },
  { label: '电子商务法', value: '电子商务法' },
]

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
  if (!file.value || !complianceStandard.value) return
  submitting.value = true
  try {
    const fd = new FormData()
    fd.append('file', file.value)
    fd.append('complianceStandard', complianceStandard.value)
    if (industry.value) fd.append('industry', industry.value)
    if (jurisdiction.value) fd.append('jurisdiction', jurisdiction.value)
    
    const data = await complianceApi.upload(fd)
    message.success('合规检查完成')
    router.push(`/compliance/${data.id}`)
  } catch (e: any) {
    message.error('请求失败: ' + e.message)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.compliance-card {
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
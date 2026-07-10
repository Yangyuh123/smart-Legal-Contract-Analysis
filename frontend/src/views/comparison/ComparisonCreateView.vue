<template>
  <div class="compare-page sl-page">
    <div class="page-header">
      <div class="sl-page-title">合同比对</div>
      <div class="sl-page-subtitle">上传两份合同文件，AI 识别新增、删除和修改内容</div>
    </div>

    <n-grid :cols="24" :x-gap="16" item-responsive responsive="screen">
      <n-gi span="24 m:11">
        <n-card :bordered="false" class="panel">
          <template #header>
            <n-tag type="primary">文件 A</n-tag>
            <span class="panel-label">上传合同A（原版）</span>
          </template>
          <n-upload :default-upload="false" :max="1" accept=".pdf,.docx,.doc,.txt" @change="(e: any) => onChange(e, 'A')">
            <n-upload-dragger>
              <div style="margin-bottom: 8px;"><n-icon :size="38" :depth="3"><CloudUploadOutline /></n-icon></div>
              <n-text>点击或拖拽文件上传</n-text>
              <n-p depth="3" style="margin: 4px 0 0;">支持 PDF / DOCX / TXT</n-p>
            </n-upload-dragger>
          </n-upload>
          <p v-if="fileA" class="file-name"><n-icon :component="DocumentTextOutline" /> {{ fileA.name }}</p>
        </n-card>
      </n-gi>

      <n-gi span="24 m:2" class="center-col" />

      <n-gi span="24 m:11">
        <n-card :bordered="false" class="panel">
          <template #header>
            <n-tag type="success">文件 B</n-tag>
            <span class="panel-label">上传合同B（新版）</span>
          </template>
          <n-upload :default-upload="false" :max="1" accept=".pdf,.docx,.doc,.txt" @change="(e: any) => onChange(e, 'B')">
            <n-upload-dragger>
              <div style="margin-bottom: 8px;"><n-icon :size="38" :depth="3"><CloudUploadOutline /></n-icon></div>
              <n-text>点击或拖拽文件上传</n-text>
              <n-p depth="3" style="margin: 4px 0 0;">支持 PDF / DOCX / TXT</n-p>
            </n-upload-dragger>
          </n-upload>
          <p v-if="fileB" class="file-name"><n-icon :component="DocumentTextOutline" /> {{ fileB.name }}</p>
        </n-card>
      </n-gi>
    </n-grid>

    <div class="action-bar">
      <n-input v-model:value="reviewRequirements" type="textarea" :rows="2"
        placeholder="比对重点（可选），如：重点关注责任条款、金额变更" style="max-width:600px;margin-bottom:16px" />
      <n-button type="primary" size="large" :disabled="!fileA || !fileB" :loading="comparing" @click="handleCompare">
        <template #icon><n-icon :component="AnalyticsOutline" /></template>
        开始比对
      </n-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage, type UploadFileInfo } from 'naive-ui'
import { AnalyticsOutline, CloudUploadOutline, DocumentTextOutline } from '@vicons/ionicons5'

const router = useRouter()
const message = useMessage()
const fileA = ref<File | null>(null)
const fileB = ref<File | null>(null)
const comparing = ref(false)
const reviewRequirements = ref('')

function onChange(data: { fileList: UploadFileInfo[] }, target: 'A' | 'B') {
  const last = data.fileList[data.fileList.length - 1]
  const raw = (last?.file as File) || null
  if (target === 'A') fileA.value = raw
  else fileB.value = raw
}

async function handleCompare() {
  if (!fileA.value || !fileB.value) return
  comparing.value = true
  try {
    const fd = new FormData()
    fd.append('fileA', fileA.value)
    fd.append('fileB', fileB.value)
    if (reviewRequirements.value.trim()) {
      fd.append('reviewRequirements', reviewRequirements.value.trim())
    }
    const token = localStorage.getItem('access_token')
    const resp = await fetch('/api/v1/comparisons/upload', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: fd,
    })
    const data = await resp.json()
    if (data.code === 200) router.push(`/compare/${data.data.compareId}`)
    else message.error(data.message || '比对失败')
  } catch (e: any) {
    message.error('请求失败: ' + e.message)
  } finally {
    comparing.value = false
  }
}
</script>

<style scoped>
.page-header { text-align: center; margin-bottom: 24px; }
.panel { min-height: 240px; }
.panel-label { margin-left: 10px; font-weight: 600; color: var(--sl-text-1); }
.center-col { display: flex; align-items: center; justify-content: center; }
.file-name { margin-top: 10px; font-size: 13px; color: #059669; display: flex; align-items: center; gap: 4px; }
.action-bar { display: flex; flex-direction: column; align-items: center; margin-top: 24px; gap: 12px; }
</style>

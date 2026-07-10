<template>
  <div class="kb-page sl-page">
    <div class="sl-flex-between" style="margin-bottom: 20px;">
      <div>
        <div class="sl-page-title">知识库</div>
        <div class="sl-page-subtitle">上传法律文档，构建知识库，基于文档内容进行智能问答</div>
      </div>
      <n-button type="primary" @click="showUpload = true">
        <template #icon><n-icon :component="CloudUploadOutline" /></template>
        上传文档
      </n-button>
    </div>

    <!-- 文档列表 -->
    <n-card :bordered="false" :title="`文档列表（${total} 篇）`">
      <n-spin :show="loading">
        <n-data-table
          :columns="columns"
          :data="docs"
          :bordered="false"
          :row-key="(row: any) => row.id"
        />
        <div class="pagination" v-if="total > size">
          <n-pagination
            v-model:page="page"
            :page-size="size"
            :item-count="total"
            @update:page="load"
          />
        </div>
      </n-spin>
    </n-card>

    <!-- 上传弹窗 -->
    <n-modal
      v-model:show="showUpload"
      preset="card"
      title="上传知识文档"
      style="width: 480px;"
    >
      <n-form :model="uploadForm" label-placement="top">
        <n-form-item label="文档标题" required>
          <n-input v-model:value="uploadForm.title" placeholder="输入文档标题" />
        </n-form-item>
        <n-form-item label="分类">
          <n-select v-model:value="uploadForm.category" :options="categoryOptions" />
        </n-form-item>
        <n-form-item label="文件" required>
          <n-upload
            :default-upload="false"
            :max="1"
            accept=".pdf,.docx,.doc,.txt,.md"
            @change="handleFileChange"
          >
            <n-upload-dragger>
              <div style="margin-bottom: 8px;">
                <n-icon :size="40" :depth="3"><CloudUploadOutline /></n-icon>
              </div>
              <n-text style="font-size: 14px;">点击或拖拽文件到此处上传</n-text>
              <n-p depth="3" style="margin: 6px 0 0;">支持 PDF / DOCX / DOC / TXT / MD</n-p>
            </n-upload-dragger>
          </n-upload>
        </n-form-item>
      </n-form>
      <template #footer>
        <div style="display:flex; justify-content:flex-end; gap:12px;">
          <n-button @click="showUpload = false">取消</n-button>
          <n-button type="primary" :loading="uploading" @click="handleUpload">确认上传</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, h, onMounted } from 'vue'
import { NButton, NTag, NPopconfirm, NIcon, useMessage, type DataTableColumns, type UploadFileInfo } from 'naive-ui'
import { CloudUploadOutline } from '@vicons/ionicons5'
import { knowledgeApi } from '@/api/knowledge'

const message = useMessage()

const showUpload = ref(false)
const loading = ref(false)
const uploading = ref(false)
const docs = ref<any[]>([])
const page = ref(1)
const size = ref(10)
const total = ref(0)
const upFile = ref<File | null>(null)
const uploadForm = ref({ title: '', category: '法律法规' })

const categoryOptions = ['法律法规', '司法解释', '合同范本', '案例分析', '其他'].map(v => ({ label: v, value: v }))

const columns: DataTableColumns<any> = [
  { title: '文档名称', key: 'title', minWidth: 200, ellipsis: { tooltip: true } },
  {
    title: '分类',
    key: 'category',
    width: 120,
    render: (row) => h(NTag, { size: 'small', round: true }, { default: () => row.category || '未分类' }),
  },
  { title: '分块数', key: 'chunkCount', width: 90, align: 'center' },
  {
    title: '状态',
    key: 'status',
    width: 100,
    align: 'center',
    render: (row) =>
      h(NTag, { type: row.status === 1 ? 'success' : 'default', size: 'small', round: true },
        { default: () => (row.status === 1 ? '已索引' : '未索引') }),
  },
  {
    title: '上传时间',
    key: 'createTime',
    width: 170,
    render: (row) => row.createTime?.substring(0, 16) || '-',
  },
  {
    title: '操作',
    key: 'actions',
    width: 90,
    align: 'center',
    render: (row) =>
      h(
        NPopconfirm,
        { onPositiveClick: () => handleDelete(row) },
        {
          trigger: () => h(NButton, { text: true, type: 'error', size: 'small' }, { default: () => '删除' }),
          default: () => '确定删除此文档？',
        },
      ),
  },
]

function handleFileChange(data: { fileList: UploadFileInfo[] }) {
  const last = data.fileList[data.fileList.length - 1]
  upFile.value = (last?.file as File) || null
}

async function load() {
  loading.value = true
  try {
    const res: any = await knowledgeApi.listDocs({ page: page.value, size: size.value })
    docs.value = res.records || []
    total.value = res.total || 0
  } catch {
    docs.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

async function handleUpload() {
  if (!upFile.value || !uploadForm.value.title) {
    message.warning('请填写标题并选择文件')
    return
  }
  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('file', upFile.value)
    fd.append('title', uploadForm.value.title)
    fd.append('category', uploadForm.value.category)
    await knowledgeApi.uploadDoc(fd)
    message.success('上传成功，正在索引...')
    showUpload.value = false
    upFile.value = null
    uploadForm.value.title = ''
    load()
  } catch (e: any) {
    message.error('上传失败: ' + (e?.message || ''))
  } finally {
    uploading.value = false
  }
}

async function handleDelete(row: any) {
  try {
    await knowledgeApi.deleteDoc(row.id)
    message.success('已删除')
    load()
  } catch { /* ignore */ }
}

onMounted(() => load())
</script>

<style scoped>
.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>

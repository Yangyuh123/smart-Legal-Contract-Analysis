import { ref } from 'vue'
import { ElMessage } from 'element-plus'

/**
 * 文件上传组合式函数
 *
 * 封装文件选择、类型/大小校验、上传状态跟踪以及进度上报，
 * 同时提供与 Element Plus 的 el-upload 组件兼容的 beforeUpload 校验函数。
 *
 * @param options  可选的配置项
 * @param options.maxSize   单文件最大字节数，默认 10 MB
 * @param options.accept    MIME 类型白名单（逗号分隔），例如 ".pdf,.doc,.docx"
 *
 * @example
 * ```vue
 * <el-upload :before-upload="beforeUpload" :http-request="customUpload">
 * ```
 */
export function useFileUpload(options?: {
  maxSize?: number
  accept?: string
}) {
  const maxSize = options?.maxSize ?? 10 * 1024 * 1024 // 默认 10 MB
  const accept = options?.accept ?? ''

  const fileList = ref<File[]>([])
  const uploading = ref(false)
  const progress = ref(0) // 0 ~ 100
  const error = ref<string | null>(null)

  // ---- 校验 ----

  /** 校验单个文件的类型与大小，返回是否通过 */
  function validateFile(file: File): boolean {
    // 1. 类型校验
    if (accept) {
      const allowedExtensions = accept
        .split(',')
        .map((s) => s.trim().toLowerCase())

      const fileName = file.name.toLowerCase()
      const matched = allowedExtensions.some((ext) => {
        // 支持 .pdf 和 application/pdf 两种写法
        if (ext.startsWith('.')) {
          return fileName.endsWith(ext)
        }
        return file.type === ext
      })

      if (!matched) {
        error.value = `不支持的文件类型 "${file.name}"，允许的类型: ${accept}`
        return false
      }
    }

    // 2. 大小校验
    if (file.size > maxSize) {
      const maxMB = (maxSize / 1024 / 1024).toFixed(1)
      error.value = `文件 "${file.name}" 超过限制 (${maxMB} MB)`
      return false
    }

    error.value = null
    return true
  }

  // ---- 文件管理 ----

  /** 处理文件选择（可手动调用，也可通过 el-upload 的 onChange 调用） */
  function handleFileSelect(file: File): boolean {
    if (!validateFile(file)) {
      ElMessage.error(error.value!)
      return false
    }
    fileList.value.push(file)
    return true
  }

  /** 从文件列表中移除指定索引的文件 */
  function handleFileRemove(index: number): void {
    if (index >= 0 && index < fileList.value.length) {
      fileList.value.splice(index, 1)
    }
  }

  /** 清空全部文件 */
  function clearFiles(): void {
    fileList.value = []
    error.value = null
    progress.value = 0
  }

  // ---- 上传 ----

  /**
   * 将所有已选文件打包为 FormData 并通过传入的 fn 发送。
   *
   * @param uploadFn  接收 FormData 并返回 Promise 的上传函数（通常是 API 层方法），
   *                  支持返回包含进度信息的响应。
   * @param fieldName FormData 中的文件字段名，默认 "file"
   */
  async function upload(
    uploadFn: (formData: FormData) => Promise<any>,
    fieldName: string = 'file',
  ): Promise<boolean> {
    if (fileList.value.length === 0) {
      ElMessage.warning('请先选择文件')
      return false
    }

    uploading.value = true
    progress.value = 0
    error.value = null

    try {
      const formData = new FormData()
      // 单文件模式（多数场景）
      if (fileList.value.length === 1) {
        formData.append(fieldName, fileList.value[0])
      } else {
        // 多文件：按 fieldName[] 的方式附加
        fileList.value.forEach((file) => {
          formData.append(fieldName, file)
        })
      }

      // 模拟进度：开始上传
      progress.value = 10

      const res = await uploadFn(formData)

      // 上传完成
      progress.value = 100
      ElMessage.success('文件上传成功')
      clearFiles()
      return true
    } catch (err: any) {
      const msg = err?.response?.data?.message || err?.message || '文件上传失败'
      error.value = msg
      ElMessage.error(msg)
      progress.value = 0
      return false
    } finally {
      uploading.value = false
    }
  }

  // ---- 与 el-upload 兼容的钩子 ----

  /**
   * 作为 el-upload 的 :before-upload 使用
   * 返回 false 会阻止上传，返回 true 允许继续
   */
  function beforeUpload(rawFile: File): boolean {
    return validateFile(rawFile)
  }

  // ---- expose ----
  return {
    fileList,
    uploading,
    progress,
    error,
    handleFileSelect,
    handleFileRemove,
    clearFiles,
    upload,
    beforeUpload,
  }
}

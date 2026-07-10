<template>
  <div class="pagination-wrapper" v-if="total > 0">
    <n-pagination
      v-model:page="innerPage"
      :page-size="innerSize"
      :page-count="Math.ceil(total / innerSize)"
      :page-sizes="pageSizes"
      show-size-picker
      :disabled="disabled"
      @update:page="handlePageChange"
      @update:page-size="handleSizeChange"
    >
      <template #prefix="{ itemCount }">共 {{ itemCount }} 项</template>
    </n-pagination>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = withDefaults(
  defineProps<{
    currentPage?: number
    pageSize?: number
    total?: number
    pageSizes?: number[]
    disabled?: boolean
  }>(),
  {
    currentPage: 1,
    pageSize: 10,
    total: 0,
    pageSizes: () => [10, 20, 50, 100],
    disabled: false,
  },
)

const emit = defineEmits<{
  (e: 'update:currentPage', value: number): void
  (e: 'update:pageSize', value: number): void
  (e: 'page-change', page: number): void
  (e: 'size-change', size: number): void
}>()

const innerPage = ref(props.currentPage)
const innerSize = ref(props.pageSize)

watch(() => props.currentPage, v => { innerPage.value = v })
watch(() => props.pageSize, v => { innerSize.value = v })

function handlePageChange(page: number) {
  emit('update:currentPage', page)
  emit('page-change', page)
}

function handleSizeChange(size: number) {
  innerPage.value = 1
  emit('update:pageSize', size)
  emit('size-change', size)
  emit('update:currentPage', 1)
}
</script>

<style scoped>
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-top: 16px;
}
</style>

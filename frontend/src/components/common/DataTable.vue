<template>
  <div class="data-table">
    <!-- 表格操作区域（搜索栏等） -->
    <div v-if="$slots.toolbar" class="table-toolbar">
      <slot name="toolbar" />
    </div>

    <!-- 表格主体 -->
    <el-table
      ref="tableRef"
      v-loading="loading"
      :data="data"
      :border="bordered"
      :stripe="stripe"
      :height="height"
      :row-key="rowKey"
      :default-sort="defaultSort"
      :empty-text="emptyText"
      element-loading-text="数据加载中..."
      element-loading-background="rgba(255, 255, 255, 0.8)"
      @selection-change="handleSelectionChange"
      @row-click="handleRowClick"
      @sort-change="handleSortChange"
    >
      <!-- 多选列 -->
      <el-table-column
        v-if="showSelection"
        type="selection"
        width="50"
        align="center"
        :reserve-selection="true"
      />

      <!-- 序号列 -->
      <el-table-column
        v-if="showIndex"
        type="index"
        label="序号"
        width="60"
        align="center"
      />

      <!-- 动态列 -->
      <el-table-column
        v-for="col in columns"
        :key="col.prop"
        :prop="col.prop"
        :label="col.label"
        :width="col.width"
        :min-width="col.minWidth"
        :sortable="col.sortable"
        :fixed="col.fixed"
        :align="col.align || 'left'"
        :show-overflow-tooltip="col.showOverflowTooltip !== false"
        :formatter="col.formatter"
      >
        <!-- 自定义列渲染的默认插槽 -->
        <template v-if="col.slot || $slots[col.prop]" #default="scope">
          <slot :name="col.slot || col.prop" :row="scope.row" :column="col" :$index="scope.$index" />
        </template>
      </el-table-column>

      <!-- 默认插槽：用于自定义列（如操作列） -->
      <slot />
    </el-table>

    <!-- append 插槽：在表格 body 之后插入内容 -->
    <slot name="append" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { TableInstance } from 'element-plus'

// -------------------------------------------------------------------
// 类型定义
// -------------------------------------------------------------------
export interface TableColumn {
  prop: string
  label: string
  width?: string | number
  minWidth?: string | number
  sortable?: boolean | 'custom'
  fixed?: boolean | 'left' | 'right'
  align?: 'left' | 'center' | 'right'
  showOverflowTooltip?: boolean
  formatter?: (row: any, column: any, cellValue: any, index: number) => string
  /** 自定义插槽名，若不传则使用 prop 作为插槽名 */
  slot?: string
}

// -------------------------------------------------------------------
// Props
// -------------------------------------------------------------------
const props = withDefaults(
  defineProps<{
    /** 表格数据 */
    data: any[]
    /** 列配置 */
    columns: TableColumn[]
    /** 是否显示加载状态 */
    loading?: boolean
    /** 空数据提示文本 */
    emptyText?: string
    /** 是否显示多选列 */
    showSelection?: boolean
    /** 是否显示序号列 */
    showIndex?: boolean
    /** 是否显示边框 */
    bordered?: boolean
    /** 是否显示斑马条纹 */
    stripe?: boolean
    /** 表格高度 */
    height?: string | number
    /** 行数据的 key */
    rowKey?: string
    /** 默认排序 */
    defaultSort?: { prop: string; order: 'ascending' | 'descending' }
  }>(),
  {
    loading: false,
    emptyText: '暂无数据',
    showSelection: false,
    showIndex: false,
    bordered: true,
    stripe: true,
    rowKey: 'id',
  },
)

// -------------------------------------------------------------------
// Emits
// -------------------------------------------------------------------
const emit = defineEmits<{
  (e: 'selection-change', rows: any[]): void
  (e: 'row-click', row: any, column: any, event: MouseEvent): void
  (e: 'sort-change', sortInfo: { prop: string; order: 'ascending' | 'descending' | null }): void
}>()

// -------------------------------------------------------------------
// 模板引用
// -------------------------------------------------------------------
const tableRef = ref<TableInstance>()

// -------------------------------------------------------------------
// 事件处理
// -------------------------------------------------------------------
function handleSelectionChange(rows: any[]) {
  emit('selection-change', rows)
}

function handleRowClick(row: any, column: any, event: MouseEvent) {
  emit('row-click', row, column, event)
}

function handleSortChange(sortInfo: { prop: string; order: 'ascending' | 'descending' | null }) {
  emit('sort-change', sortInfo)
}

// -------------------------------------------------------------------
// 暴露方法
// -------------------------------------------------------------------
defineExpose({
  /** 获取 el-table 实例 */
  tableRef,
  /** 清空选中 */
  clearSelection() {
    tableRef.value?.clearSelection()
  },
  /** 切换行选中状态 */
  toggleRowSelection(row: any, selected?: boolean) {
    tableRef.value?.toggleRowSelection(row, selected)
  },
  /** 全选 / 清空全选 */
  toggleAllSelection() {
    tableRef.value?.toggleAllSelection()
  },
})
</script>

<style scoped lang="scss">
.data-table {
  width: 100%;

  .table-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
    flex-wrap: wrap;
    gap: 12px;
  }

  :deep(.el-table) {
    // 表头样式
    .el-table__header-wrapper {
      th.el-table__cell {
        background-color: #fafbfc;
        color: #606266;
        font-weight: 600;
        font-size: 13px;
        height: 48px;
      }
    }

    // 行样式
    .el-table__row {
      cursor: default;

      &.el-table__row--striped {
        td.el-table__cell {
          background-color: #fafbfc;
        }
      }

      &:hover > td.el-table__cell {
        background-color: #f0f4ff;
      }
    }

    // 单元格
    td.el-table__cell {
      font-size: 14px;
      color: #303133;
      height: 48px;
    }
  }

  // 空状态样式
  :deep(.el-table__empty-block) {
    min-height: 200px;
  }

  :deep(.el-table__empty-text) {
    color: #909399;
    font-size: 14px;
    line-height: 1.5;
  }
}
</style>

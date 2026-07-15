<template>
  <el-tag
    :type="tagType"
    :size="size"
    :effect="effect"
    :round="round"
    :hit="hit"
    class="status-badge"
    :class="`status-badge--${tagType}`"
  >
    <el-icon v-if="showDot" class="status-dot" :size="10">
      <component :is="dotIcon" />
    </el-icon>
    <span class="status-label">{{ label }}</span>
  </el-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { CircleCheckFilled, CircleCloseFilled, WarningFilled, InfoFilled } from '@element-plus/icons-vue'

// -------------------------------------------------------------------
// 类型定义
// -------------------------------------------------------------------

/** 合同状态枚举 */
type ContractStatus = 'DRAFT' | 'ACTIVE' | 'ARCHIVED'

/** 审查状态枚举 */
type ReviewStatus = 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED'

/** 合规状态枚举 */
type ComplianceStatus = 'PENDING' | 'IN_PROGRESS' | 'PASSED' | 'FAILED' | 'EXEMPTED'

/** 通知状态枚举 */
type NotificationStatus = 'UNREAD' | 'READ' | 'ARCHIVED'

/** 组件支持的所有状态值 */
type StatusValue = ContractStatus | ReviewStatus | ComplianceStatus | NotificationStatus | string

/** 分类类型 */
type CategoryType = 'contract' | 'review' | 'compliance' | 'notification'

// -------------------------------------------------------------------
// 状态映射数据
// -------------------------------------------------------------------

interface StatusEntry {
  label: string
  type: 'success' | 'info' | 'warning' | 'danger' | 'primary' | ''
}

/** 合同状态映射 */
const contractStatusMap: Record<ContractStatus, StatusEntry> = {
  DRAFT: { label: '草稿', type: 'info' },
  ACTIVE: { label: '生效', type: 'success' },
  ARCHIVED: { label: '归档', type: 'warning' },
}

/** 审查状态映射 */
const reviewStatusMap: Record<ReviewStatus, StatusEntry> = {
  PENDING: { label: '待审查', type: 'info' },
  PROCESSING: { label: '审查中', type: 'warning' },
  COMPLETED: { label: '已完成', type: 'success' },
  FAILED: { label: '失败', type: 'danger' },
}

/** 合规状态映射 */
const complianceStatusMap: Record<ComplianceStatus, StatusEntry> = {
  PENDING: { label: '待检查', type: 'info' },
  IN_PROGRESS: { label: '检查中', type: 'warning' },
  PASSED: { label: '已通过', type: 'success' },
  FAILED: { label: '未通过', type: 'danger' },
  EXEMPTED: { label: '已豁免', type: 'info' },
}

/** 通知状态映射 */
const notificationStatusMap: Record<NotificationStatus, StatusEntry> = {
  UNREAD: { label: '未读', type: 'danger' },
  READ: { label: '已读', type: 'info' },
  ARCHIVED: { label: '已归档', type: 'warning' },
}

/** 综合状态映射表 */
const statusMaps: Record<CategoryType, Record<string, StatusEntry>> = {
  contract: contractStatusMap,
  review: reviewStatusMap,
  compliance: complianceStatusMap,
  notification: notificationStatusMap,
}

/** 状态点图标映射 */
const dotIconMap: Record<string, typeof CircleCheckFilled> = {
  success: CircleCheckFilled,
  info: InfoFilled,
  warning: WarningFilled,
  danger: CircleCloseFilled,
}

// -------------------------------------------------------------------
// Props
// -------------------------------------------------------------------
const props = withDefaults(
  defineProps<{
    /** 状态值 */
    status: string
    /** 分类类型 */
    type?: CategoryType
    /** Tag 尺寸 */
    size?: 'large' | 'default' | 'small'
    /** Tag 主题 */
    effect?: 'dark' | 'light' | 'plain'
    /** 是否圆角 */
    round?: boolean
    /** 是否显示状态点 */
    showDot?: boolean
    /** 是否有边框 */
    hit?: boolean
  }>(),
  {
    type: 'contract',
    size: 'default',
    effect: 'light',
    round: false,
    showDot: true,
    hit: false,
  },
)

// -------------------------------------------------------------------
// 计算属性
// -------------------------------------------------------------------

/** 根据 type 和 status 计算出标签文本 */
const label = computed<string>(() => {
  const map = statusMaps[props.type]
  if (!map) return props.status

  const entry = map[props.status]
  return entry?.label ?? props.status
})

/** 根据 type 和 status 计算出 Element Plus tag 的 type */
const tagType = computed<string>(() => {
  const map = statusMaps[props.type]
  if (!map) return 'info'

  const entry = map[props.status]
  return entry?.type ?? 'info'
})

/** 状态点图标 */
const dotIcon = computed(() => {
  return dotIconMap[tagType.value] ?? InfoFilled
})

</script>

<style scoped lang="scss">
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-weight: 500;
  white-space: nowrap;

  .status-dot {
    flex-shrink: 0;
  }

  .status-label {
    line-height: 1;
  }

  // ---- 颜色微调 ----
  &--success {
    --el-tag-bg-color: rgba(38, 162, 105, 0.1);
    --el-tag-border-color: rgba(38, 162, 105, 0.2);
    --el-tag-text-color: #1b8151;
  }

  &--warning {
    --el-tag-bg-color: rgba(229, 165, 10, 0.1);
    --el-tag-border-color: rgba(229, 165, 10, 0.2);
    --el-tag-text-color: #b8860b;
  }

  &--danger {
    --el-tag-bg-color: rgba(192, 28, 40, 0.1);
    --el-tag-border-color: rgba(192, 28, 40, 0.2);
    --el-tag-text-color: #99161f;
  }

  &--info {
    --el-tag-bg-color: rgba(144, 147, 153, 0.1);
    --el-tag-border-color: rgba(144, 147, 153, 0.2);
    --el-tag-text-color: #606266;
  }

  &--primary {
    --el-tag-bg-color: rgba(26, 95, 180, 0.1);
    --el-tag-border-color: rgba(26, 95, 180, 0.2);
    --el-tag-text-color: #144b8c;
  }
}
</style>

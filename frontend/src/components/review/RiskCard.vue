<template>
  <el-card
    class="risk-card"
    :class="[`risk-card--${riskLevelClass}`, { 'risk-card--expanded': isExpanded }]"
    shadow="hover"
  >
    <!-- 卡片头部：风险编号 + 标题 + 等级标签 -->
    <div class="risk-card__header" @click="toggleExpand">
      <div class="risk-card__header-left">
        <span class="risk-card__badge" :class="`risk-card__badge--${riskLevelClass}`">
          {{ index + 1 }}
        </span>
        <span class="risk-card__title">{{ risk.title }}</span>
        <el-tag
          :type="riskTagType"
          size="small"
          effect="light"
          class="risk-card__level-tag"
        >
          {{ riskLevelLabel }}
        </el-tag>
      </div>
      <div class="risk-card__header-right">
        <span class="risk-card__location">
          <el-icon><Location /></el-icon>
          {{ risk.location }}
        </span>
        <el-button
          :icon="isExpanded ? ArrowUp : ArrowDown"
          text
          size="small"
          class="risk-card__toggle-btn"
        >
          {{ isExpanded ? '收起' : '展开' }}
        </el-button>
      </div>
    </div>

    <!-- 风险描述 -->
    <div class="risk-card__description">
      <p>{{ risk.description }}</p>
    </div>

    <!-- 展开详情 -->
    <el-collapse-transition>
      <div v-show="isExpanded" class="risk-card__details">
        <el-divider />
        <div class="risk-card__detail-section">
          <h4 class="risk-card__detail-label">
            <el-icon><Document /></el-icon>
            合同原文
          </h4>
          <div class="risk-card__detail-content risk-card__detail-content--quote">
            {{ risk.originalText }}
          </div>
        </div>

        <div class="risk-card__detail-section">
          <h4 class="risk-card__detail-label">
            <el-icon><Edit /></el-icon>
            修改建议
          </h4>
          <div class="risk-card__detail-content risk-card__detail-content--suggestion">
            {{ risk.suggestion }}
          </div>
        </div>

        <div v-if="risk.relatedClause" class="risk-card__detail-section">
          <h4 class="risk-card__detail-label">
            <el-icon><Collection /></el-icon>
            相关法规条款
          </h4>
          <div class="risk-card__detail-content risk-card__detail-content--clause">
            {{ risk.relatedClause }}
          </div>
        </div>

        <!-- 已忽略标记 -->
        <div v-if="risk.isIgnored" class="risk-card__ignored-banner">
          <el-icon><WarningFilled /></el-icon>
          该风险项已被标记为忽略
        </div>
      </div>
    </el-collapse-transition>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  Location,
  ArrowDown,
  ArrowUp,
  Document,
  Edit,
  Collection,
  WarningFilled,
} from '@element-plus/icons-vue'
import type { ReviewRisk } from '@/types/review'
import { RiskLevel } from '@/types/review'

interface Props {
  risk: ReviewRisk
  index: number
  expanded?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  expanded: false,
})

const isExpanded = ref(props.expanded)

function toggleExpand() {
  isExpanded.value = !isExpanded.value
}

/** Risk level CSS class */
const riskLevelClass = computed(() => {
  switch (props.risk.riskLevel) {
    case RiskLevel.HIGH:
      return 'high'
    case RiskLevel.MEDIUM:
      return 'medium'
    case RiskLevel.LOW:
      return 'low'
    default:
      return 'low'
  }
})

/** Risk level Chinese label */
const riskLevelLabel = computed(() => {
  switch (props.risk.riskLevel) {
    case RiskLevel.HIGH:
      return '高风险'
    case RiskLevel.MEDIUM:
      return '中风险'
    case RiskLevel.LOW:
      return '低风险'
    default:
      return '未知'
  }
})

/** Element Plus tag type */
const riskTagType = computed(() => {
  switch (props.risk.riskLevel) {
    case RiskLevel.HIGH:
      return 'danger'
    case RiskLevel.MEDIUM:
      return 'warning'
    case RiskLevel.LOW:
      return 'success'
    default:
      return 'info'
  }
})
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.risk-card {
  margin-bottom: $spacing-base;
  border-left: 4px solid $color-gray-300;
  transition: all $transition-duration-base $transition-ease;
  cursor: default;

  &:hover {
    border-left-width: 6px;
  }

  // High risk
  &--high {
    border-left-color: $risk-high;
    .risk-card__badge--high {
      background-color: $risk-high;
    }
  }

  // Medium risk
  &--medium {
    border-left-color: $risk-medium;
    .risk-card__badge--medium {
      background-color: $risk-medium;
    }
  }

  // Low risk
  &--low {
    border-left-color: $risk-low;
    .risk-card__badge--low {
      background-color: $risk-low;
    }
  }

  // Expanded state
  &--expanded {
    border-left-width: 6px;
  }

  :deep(.el-card__body) {
    padding: $spacing-base $spacing-xl;
  }
}

// 卡片头部
.risk-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  user-select: none;
  flex-wrap: wrap;
  gap: $spacing-sm;
}

.risk-card__header-left {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  flex: 1;
  min-width: 0;
}

.risk-card__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: $radius-full;
  color: $color-white;
  font-size: $font-size-xs;
  font-weight: $font-weight-bold;
  flex-shrink: 0;
  line-height: 1;
}

.risk-card__title {
  font-size: $font-size-base;
  font-weight: $font-weight-semibold;
  color: $color-gray-700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}

.risk-card__level-tag {
  flex-shrink: 0;
}

.risk-card__header-right {
  display: flex;
  align-items: center;
  gap: $spacing-base;
  flex-shrink: 0;
}

.risk-card__location {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: $font-size-sm;
  color: $color-text-secondary;
}

.risk-card__toggle-btn {
  font-size: $font-size-sm;
  color: $color-primary;
  padding: 0 4px;
}

// 风险描述
.risk-card__description {
  margin-top: $spacing-sm;

  p {
    font-size: $font-size-base;
    color: $color-text-regular;
    line-height: $line-height-relaxed;
    margin: 0;
  }
}

// 展开详情
.risk-card__details {
  margin-top: $spacing-xs;
}

.risk-card__detail-section {
  margin-bottom: $spacing-base;

  &:last-child {
    margin-bottom: 0;
  }
}

.risk-card__detail-label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: $font-size-sm;
  font-weight: $font-weight-semibold;
  color: $color-gray-600;
  margin: 0 0 $spacing-sm 0;
}

.risk-card__detail-content {
  font-size: $font-size-sm;
  line-height: $line-height-relaxed;
  color: $color-text-regular;
  padding: $spacing-sm $spacing-base;
  border-radius: $radius-md;
  background-color: $color-gray-50;
  border: 1px solid $color-gray-200;

  &--quote {
    border-left: 3px solid $color-gray-300;
    font-style: italic;
    color: $color-gray-600;
  }

  &--suggestion {
    border-left: 3px solid $color-primary-light;
    color: $color-gray-700;
  }

  &--clause {
    border-left: 3px solid $color-warning;
    color: $color-gray-700;
  }
}

// 已忽略横幅
.risk-card__ignored-banner {
  display: flex;
  align-items: center;
  gap: $spacing-xs;
  padding: $spacing-sm $spacing-base;
  background-color: $color-gray-100;
  border-radius: $radius-sm;
  font-size: $font-size-sm;
  color: $color-text-secondary;
  margin-top: $spacing-base;
}

// 响应式
@media (max-width: $breakpoint-md) {
  .risk-card__header {
    flex-direction: column;
    align-items: flex-start;
  }

  .risk-card__header-right {
    width: 100%;
    justify-content: space-between;
  }
}
</style>

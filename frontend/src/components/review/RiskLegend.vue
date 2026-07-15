<template>
  <div class="risk-legend">
    <div class="risk-legend__item">
      <span class="risk-legend__dot risk-legend__dot--high"></span>
      <el-tag type="danger" size="small" effect="light">高风险</el-tag>
    </div>
    <div class="risk-legend__item">
      <span class="risk-legend__dot risk-legend__dot--medium"></span>
      <el-tag type="warning" size="small" effect="light">中风险</el-tag>
    </div>
    <div class="risk-legend__item">
      <span class="risk-legend__dot risk-legend__dot--low"></span>
      <el-tag type="success" size="small" effect="light">低风险</el-tag>
    </div>
  </div>
</template>

<script setup lang="ts">
// RiskLegend - purely presentational, no props or logic needed
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.risk-legend {
  display: flex;
  align-items: center;
  gap: $spacing-lg;
  padding: $spacing-sm 0;
  flex-wrap: wrap;
}

.risk-legend__item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.risk-legend__dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: $radius-full;
  flex-shrink: 0;

  &--high {
    background-color: $risk-high;
  }

  &--medium {
    background-color: $risk-medium;
  }

  &--low {
    background-color: $risk-low;
  }
}
</style>

<template>
  <div class="empty-state" :style="{ paddingTop: verticalOffset }">
    <!-- 插画 / 图标 -->
    <div class="empty-image" :style="{ width: imageSize + 'px', height: imageSize + 'px' }">
      <!-- 自定义图片 -->
      <img
        v-if="customImage"
        :src="customImage"
        :alt="description"
        class="empty-img"
      />
      <!-- 内置 SVG 图标 -->
      <svg
        v-else
        class="empty-svg"
        viewBox="0 0 120 120"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <!-- 盒子主体 -->
        <rect
          x="28"
          y="42"
          width="64"
          height="50"
          rx="4"
          stroke="#c0c4cc"
          stroke-width="2.5"
          fill="none"
        />
        <!-- 上盖 -->
        <rect
          x="28"
          y="30"
          width="64"
          height="16"
          rx="4"
          stroke="#c0c4cc"
          stroke-width="2.5"
          fill="#f5f6fa"
        />
        <!-- 盒子折线 -->
        <path
          d="M28 46 L60 60 L92 46"
          stroke="#c0c4cc"
          stroke-width="2"
          stroke-linejoin="round"
          fill="none"
        />
        <!-- 把手 -->
        <rect
          x="52"
          y="24"
          width="16"
          height="8"
          rx="2"
          stroke="#c0c4cc"
          stroke-width="2.5"
          fill="#f5f6fa"
        />
        <!-- 底部线条（表示空的） -->
        <line
          x1="38"
          y1="60"
          x2="82"
          y2="60"
          stroke="#dcdfe6"
          stroke-width="1.5"
          stroke-linecap="round"
        />
        <line
          x1="42"
          y1="68"
          x2="78"
          y2="68"
          stroke="#dcdfe6"
          stroke-width="1.5"
          stroke-linecap="round"
        />
      </svg>
    </div>

    <!-- 描述文本 -->
    <p class="empty-description" :style="{ maxWidth: maxDescriptionWidth }">
      {{ description }}
    </p>

    <!-- 操作按钮插槽 -->
    <div v-if="$slots.actions" class="empty-actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

// -------------------------------------------------------------------
// Props
// -------------------------------------------------------------------
const props = withDefaults(
  defineProps<{
    /** 自定义图片 URL */
    image?: string
    /** 描述文本 */
    description?: string
    /** 图片 / 图标大小（px） */
    imageSize?: number
  }>(),
  {
    image: '',
    description: '暂无数据',
    imageSize: 120,
  },
)

// -------------------------------------------------------------------
// 计算属性
// -------------------------------------------------------------------

/** 是否使用自定义图片 */
const customImage = computed(() => props.image && props.image.length > 0)

/** 垂直偏移量 */
const verticalOffset = computed(() => {
  // 较小的 image 可能需要多一点顶部空间
  if (props.imageSize <= 80) return '32px'
  return '24px'
})

/** 描述文本最大宽度 */
const maxDescriptionWidth = computed(() => {
  return `${Math.max(props.imageSize + 40, 200)}px`
})
</script>

<style scoped lang="scss">
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 40px 20px;
  width: 100%;
  box-sizing: border-box;
}

// ---- 图标 / 图片 ----
.empty-image {
  margin-bottom: 20px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;

  .empty-svg {
    width: 100%;
    height: 100%;
  }

  .empty-img {
    width: 100%;
    height: 100%;
    object-fit: contain;
  }
}

// ---- 描述文本 ----
.empty-description {
  margin: 0 0 20px 0;
  font-size: 14px;
  color: #909399;
  line-height: 1.6;
  text-align: center;
  word-break: break-word;
}

// ---- 操作按钮 ----
.empty-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 4px;
}
</style>

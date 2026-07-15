<template>
  <Teleport :to="fullscreen ? 'body' : null" :disabled="!fullscreen">
    <Transition name="loading-fade">
      <div
        v-show="loading"
        class="loading-spinner"
        :class="{ 'is-fullscreen': fullscreen, 'is-inline': !fullscreen }"
        role="alert"
        aria-busy="true"
        aria-label="加载中"
      >
        <!-- 全屏模式的背景遮罩 -->
        <div v-if="fullscreen" class="loading-mask" />

        <!-- 内容容器 -->
        <div class="loading-container">
          <!-- 旋转动画 -->
          <div class="spinner-wrapper">
            <svg class="spinner-circle" viewBox="0 0 50 50" aria-hidden="true">
              <circle
                class="spinner-track"
                cx="25"
                cy="25"
                r="20"
                fill="none"
                stroke-width="3"
              />
              <circle
                class="spinner-path"
                cx="25"
                cy="25"
                r="20"
                fill="none"
                stroke-width="3"
                stroke-linecap="round"
              />
            </svg>
          </div>

          <!-- 加载文本 -->
          <p v-if="text" class="loading-text">{{ text }}</p>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
// -------------------------------------------------------------------
// Props
// -------------------------------------------------------------------
withDefaults(
  defineProps<{
    /** 是否显示加载状态 */
    loading?: boolean
    /** 加载提示文本 */
    text?: string
    /** 是否全屏模式 */
    fullscreen?: boolean
  }>(),
  {
    loading: false,
    text: '加载中...',
    fullscreen: false,
  },
)
</script>

<style scoped lang="scss">
.loading-spinner {
  // ---- 全屏模式 ----
  &.is-fullscreen {
    position: fixed;
    inset: 0;
    z-index: 2000;
    display: flex;
    align-items: center;
    justify-content: center;

    .loading-mask {
      position: absolute;
      inset: 0;
      background-color: rgba(255, 255, 255, 0.75);
      backdrop-filter: blur(2px);
    }

    .loading-container {
      position: relative;
      z-index: 1;
      text-align: center;
      background: #ffffff;
      border-radius: 12px;
      padding: 40px 56px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }
  }

  // ---- 内联模式 ----
  &.is-inline {
    position: relative;
    min-height: 160px;
    display: flex;
    align-items: center;
    justify-content: center;

    .loading-container {
      text-align: center;
    }
  }
}

// ---- 内容容器 ----
.loading-container {
  user-select: none;
}

// ---- 旋转动画 ----
.spinner-wrapper {
  display: inline-block;
  margin-bottom: 16px;

  .spinner-circle {
    width: 48px;
    height: 48px;
    animation: spinner-rotate 1.4s linear infinite;
  }

  .spinner-track {
    stroke: #ebeef5;
  }

  .spinner-path {
    stroke: #1a5fb4;
    stroke-dasharray: 90, 150;
    stroke-dashoffset: 0;
    transform-origin: center;
    animation: spinner-dash 1.4s ease-in-out infinite;
  }
}

// ---- 文本 ----
.loading-text {
  margin: 0;
  font-size: 14px;
  color: #606266;
  line-height: 1.5;
}

// ---- 过渡动画 ----
.loading-fade-enter-active,
.loading-fade-leave-active {
  transition: opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.loading-fade-enter-from,
.loading-fade-leave-to {
  opacity: 0;
}

// ---- 关键帧 ----
@keyframes spinner-rotate {
  100% {
    transform: rotate(360deg);
  }
}

@keyframes spinner-dash {
  0% {
    stroke-dasharray: 1, 150;
    stroke-dashoffset: 0;
  }
  50% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -35;
  }
  100% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -124;
  }
}
</style>

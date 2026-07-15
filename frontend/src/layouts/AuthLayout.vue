<template>
  <div class="auth-layout">
    <div class="auth-card">
      <div class="auth-header">
        <div class="auth-logo">
          <n-icon :size="40" color="#6366f1">
            <ShieldCheckmarkOutline />
          </n-icon>
        </div>
        <h1 class="auth-title">SmartLegal</h1>
        <p class="auth-subtitle">智能合同审查与生成系统</p>
      </div>
      <router-view />
    </div>
    <div class="auth-footer">
      <span>SmartLegal &copy; 2026 智能合同审查系统</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { NIcon } from 'naive-ui'
import { ShieldCheckmarkOutline } from '@vicons/ionicons5'
</script>

<style scoped>
.auth-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #4f46e5 0%, #6366f1 40%, #818cf8 75%, #a5b4fc 100%);
  position: relative;
  overflow: hidden;
}

.auth-layout::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 20% 50%, rgba(255, 255, 255, 0.08) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(255, 255, 255, 0.06) 0%, transparent 50%);
  pointer-events: none;
}

.auth-card {
  width: 420px;
  max-width: calc(100vw - 40px);
  background: #ffffff;
  border-radius: 18px;
  padding: 48px 40px 40px;
  box-shadow:
    0 4px 6px -1px rgba(0, 0, 0, 0.08),
    0 20px 50px -12px rgba(0, 0, 0, 0.3);
  position: relative;
  z-index: 1;
}

.auth-header {
  text-align: center;
  margin-bottom: 36px;
}

.auth-logo {
  margin-bottom: 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
  border-radius: 18px;
}

.auth-title {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 8px;
  letter-spacing: -0.5px;
}

.auth-subtitle {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
  font-weight: 400;
}

.auth-footer {
  margin-top: 28px;
  text-align: center;
  color: rgba(255, 255, 255, 0.8);
  font-size: 13px;
  position: relative;
  z-index: 1;
}
</style>

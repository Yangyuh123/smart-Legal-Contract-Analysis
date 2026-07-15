<template>
  <n-config-provider :theme-overrides="themeOverrides" :locale="zhCN" :date-locale="dateZhCN">
    <n-loading-bar-provider>
      <n-message-provider>
        <n-dialog-provider>
          <n-notification-provider>
            <router-view />
          </n-notification-provider>
        </n-dialog-provider>
      </n-message-provider>
    </n-loading-bar-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { NConfigProvider, NLoadingBarProvider, NMessageProvider, NDialogProvider, NNotificationProvider, zhCN, dateZhCN } from 'naive-ui'
import { themeOverrides } from '@/theme'
</script>

<style>
#app {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}
</style>

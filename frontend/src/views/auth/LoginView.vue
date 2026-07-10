<template>
  <div class="login-view">
    <n-form
      ref="formRef"
      :model="form"
      :rules="rules"
      size="large"
      @submit.prevent="handleLogin"
    >
      <n-form-item path="username" :show-label="false">
        <n-input v-model:value="form.username" placeholder="请输入用户名" clearable>
          <template #prefix>
            <n-icon :component="PersonOutline" />
          </template>
        </n-input>
      </n-form-item>

      <n-form-item path="password" :show-label="false">
        <n-input
          v-model:value="form.password"
          type="password"
          show-password-on="click"
          placeholder="请输入密码"
          @keyup.enter="handleLogin"
        >
          <template #prefix>
            <n-icon :component="LockClosedOutline" />
          </template>
        </n-input>
      </n-form-item>

      <div class="login-options">
        <n-checkbox v-model:checked="form.rememberMe">记住我</n-checkbox>
        <n-button text type="primary" @click="handleForgotPassword">忘记密码？</n-button>
      </div>

      <n-button
        type="primary"
        size="large"
        block
        attr-type="submit"
        :loading="loading"
        class="login-btn"
        @click="handleLogin"
      >
        {{ loading ? '登录中...' : '登 录' }}
      </n-button>

      <div class="form-footer">
        <span>还没有账号？</span>
        <n-button text type="primary" @click="router.push('/auth/register')">立即注册</n-button>
      </div>
    </n-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage, type FormInst, type FormRules } from 'naive-ui'
import { PersonOutline, LockClosedOutline } from '@vicons/ionicons5'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'

const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()
const notificationStore = useNotificationStore()

const formRef = ref<FormInst | null>(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
  rememberMe: false,
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: ['blur', 'input'] },
    { min: 2, max: 50, message: '用户名长度为2-50个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: ['blur', 'input'] },
    { min: 6, max: 100, message: '密码长度至少6位', trigger: 'blur' },
  ],
}

async function handleLogin() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  loading.value = true
  try {
    await authStore.login({ username: form.username, password: form.password })
    if (form.rememberMe) {
      localStorage.setItem('remembered_username', form.username)
    } else {
      localStorage.removeItem('remembered_username')
    }
    message.success('登录成功')
    notificationStore.startPolling()
    router.push('/dashboard')
  } catch {
    message.error('用户名或密码错误')
  } finally {
    loading.value = false
  }
}

function handleForgotPassword() {
  message.info('请联系管理员重置密码')
}

// 恢复"记住我"的用户名
const remembered = localStorage.getItem('remembered_username')
if (remembered) {
  form.username = remembered
  form.rememberMe = true
}
</script>

<style scoped lang="scss">
.login-view {
  width: 100%;
}

.login-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.login-btn {
  margin-top: 4px;
  font-size: 16px;
  letter-spacing: 4px;
}

.form-footer {
  text-align: center;
  font-size: 14px;
  color: var(--sl-text-3);
  margin-top: 20px;
}
</style>

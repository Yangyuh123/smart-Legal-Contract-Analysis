<template>
  <div class="register-view">
    <n-form
      ref="formRef"
      :model="form"
      :rules="rules"
      size="large"
      @submit.prevent="handleRegister"
    >
      <n-form-item path="username" :show-label="false">
        <n-input v-model:value="form.username" placeholder="请输入用户名" clearable>
          <template #prefix><n-icon :component="PersonOutline" /></template>
        </n-input>
      </n-form-item>

      <n-form-item path="realName" :show-label="false">
        <n-input v-model:value="form.realName" placeholder="请输入真实姓名" clearable>
          <template #prefix><n-icon :component="IdCardOutline" /></template>
        </n-input>
      </n-form-item>

      <n-form-item path="email" :show-label="false">
        <n-input v-model:value="form.email" placeholder="请输入邮箱地址" clearable>
          <template #prefix><n-icon :component="MailOutline" /></template>
        </n-input>
      </n-form-item>

      <n-form-item path="phone" :show-label="false">
        <n-input v-model:value="form.phone" placeholder="请输入手机号码" clearable>
          <template #prefix><n-icon :component="CallOutline" /></template>
        </n-input>
      </n-form-item>

      <n-form-item path="password" :show-label="false">
        <n-input
          v-model:value="form.password"
          type="password"
          show-password-on="click"
          placeholder="请输入密码"
        >
          <template #prefix><n-icon :component="LockClosedOutline" /></template>
        </n-input>
      </n-form-item>

      <n-form-item path="confirmPassword" :show-label="false">
        <n-input
          v-model:value="form.confirmPassword"
          type="password"
          show-password-on="click"
          placeholder="请确认密码"
          @keyup.enter="handleRegister"
        >
          <template #prefix><n-icon :component="LockClosedOutline" /></template>
        </n-input>
      </n-form-item>

      <n-button
        type="primary"
        size="large"
        block
        attr-type="submit"
        :loading="loading"
        class="register-btn"
        @click="handleRegister"
      >
        {{ loading ? '注册中...' : '注 册' }}
      </n-button>

      <div class="form-footer">
        <span>已有账号？</span>
        <n-button text type="primary" @click="router.push('/auth/login')">立即登录</n-button>
      </div>
    </n-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage, type FormInst, type FormItemRule, type FormRules } from 'naive-ui'
import { PersonOutline, LockClosedOutline, MailOutline, IdCardOutline, CallOutline } from '@vicons/ionicons5'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import { authApi } from '@/api/auth'

const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()
const notificationStore = useNotificationStore()

const formRef = ref<FormInst | null>(null)
const loading = ref(false)

const form = reactive({
  username: '',
  realName: '',
  email: '',
  phone: '',
  password: '',
  confirmPassword: '',
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: ['blur', 'input'] },
    { min: 2, max: 50, message: '用户名长度为2-50个字符', trigger: 'blur' },
    {
      pattern: /^[一-龥a-zA-Z0-9_]+$/,
      message: '用户名只能包含中文、字母、数字和下划线',
      trigger: 'blur',
    },
  ],
  realName: [
    { required: true, message: '请输入真实姓名', trigger: 'blur' },
    { min: 2, max: 30, message: '姓名长度为2-30个字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: ['blur', 'input'] },
  ],
  phone: [
    { required: true, message: '请输入手机号码', trigger: 'blur' },
    {
      validator: (_rule: FormItemRule, value: string) => {
        if (!value) return true
        return /^1[3-9]\d{9}$/.test(value)
      },
      message: '请输入有效的手机号码',
      trigger: 'blur',
    },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度为6-20个字符', trigger: 'blur' },
    {
      pattern: /^(?=.*[a-zA-Z])(?=.*\d)/,
      message: '密码必须包含字母和数字',
      trigger: 'blur',
    },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (_rule: FormItemRule, value: string) => value === form.password,
      message: '两次输入的密码不一致',
      trigger: ['blur', 'input'],
    },
  ],
}

async function handleRegister() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  loading.value = true
  try {
    await authApi.register({
      username: form.username,
      password: form.password,
      email: form.email,
      realName: form.realName,
      phone: form.phone,
    })
    message.success('注册成功，正在自动登录...')

    try {
      await authStore.login({ username: form.username, password: form.password })
      notificationStore.startPolling()
      router.push('/dashboard')
    } catch {
      message.warning('注册成功，请手动登录')
      router.push('/auth/login')
    }
  } catch {
    message.error('注册失败，请稍后重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.register-view {
  width: 100%;
}

.register-btn {
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

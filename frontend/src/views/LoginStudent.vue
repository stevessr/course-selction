<template>
  <div class="login-container">
    <a-card class="login-card">
      <template #title>
        <div class="login-header">
          <BookOutlined style="font-size: 24px; margin-right: 8px;" />
          <span>Student Login</span>
        </div>
      </template>
      
      <!-- Phase 1: Username & Password -->
      <a-form
        v-if="!needsTwoFactor"
        :model="loginForm"
        @finish="handleLogin"
        layout="vertical"
      >
        <a-form-item
          label="Username"
          name="username"
          :rules="[{ required: true, message: 'Please input your username!' }]"
        >
          <a-input v-model:value="loginForm.username" placeholder="Username" size="large" />
        </a-form-item>

        <a-form-item
          label="Password"
          name="password"
          :rules="[{ required: true, message: 'Please input your password!' }]"
        >
          <a-input-password v-model:value="loginForm.password" placeholder="Password" size="large" />
        </a-form-item>

        <a-form-item>
          <a-button type="primary" html-type="submit" block :loading="loading" size="large">
            Login
          </a-button>
        </a-form-item>

        <a-form-item>
          <a-space direction="vertical" style="width: 100%">
            <router-link to="/register">Don't have an account? Register</router-link>
            <router-link to="/login">Back to login selection</router-link>
          </a-space>
        </a-form-item>
      </a-form>

      <!-- Phase 2: 2FA Verification -->
      <a-form v-else :model="twoFactorForm" @finish="handleTwoFactor" layout="vertical">
        <a-alert
          message="Two-Factor Authentication Required"
          description="Please enter the 6-digit code from your authenticator app."
          type="info"
          show-icon
          style="margin-bottom: 16px"
        />

        <a-form-item
          label="2FA Code"
          name="totpCode"
          :rules="[{ required: true, message: 'Please input your 2FA code!' }]"
        >
          <a-input
            v-model:value="twoFactorForm.totpCode"
            placeholder="000000"
            maxlength="6"
            size="large"
          />
        </a-form-item>

        <a-form-item>
          <a-button type="primary" html-type="submit" block :loading="loading" size="large">
            Verify
          </a-button>
        </a-form-item>

        <a-form-item>
          <a-button type="link" block @click="cancelTwoFactor">
            Cancel
          </a-button>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { BookOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const authStore = useAuthStore()

const loginForm = ref({
  username: '',
  password: '',
})

const twoFactorForm = ref({
  totpCode: '',
})

const loading = ref(false)
const needsTwoFactor = ref(false)

const handleLogin = async () => {
  loading.value = true
  try {
    const result = await authStore.login(loginForm.value.username, loginForm.value.password)
    if (result.success) {
      needsTwoFactor.value = true
    } else {
      message.error(result.error || 'Login failed')
    }
  } catch (error) {
    message.error(error.message || 'Login failed')
  } finally {
    loading.value = false
  }
}

const handleTwoFactor = async () => {
  loading.value = true
  try {
    await authStore.verify2FA(twoFactorForm.value.totpCode)
    message.success('Login successful')
    router.push('/student/courses')
  } catch (error) {
    message.error(error.message || '2FA verification failed')
  } finally {
    loading.value = false
  }
}

const cancelTwoFactor = () => {
  needsTwoFactor.value = false
  loginForm.value = { username: '', password: '' }
  twoFactorForm.value = { totpCode: '' }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 100%;
  max-width: 400px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.login-header {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: bold;
}
</style>

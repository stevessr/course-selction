<template>
  <div class="login-container">
    <a-card class="login-card">
      <template #title>
        <div class="login-header">
          <ReadOutlined style="font-size: 24px; margin-right: 8px;" />
          <span>Teacher Login</span>
        </div>
      </template>
      
      <!-- Username & Password Login -->
      <a-form
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
          <router-link to="/login">Back to login selection</router-link>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { ReadOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const authStore = useAuthStore()

const loginForm = ref({
  username: '',
  password: '',
})

const loading = ref(false)

// Check if we have a valid refresh token on mount
onMounted(async () => {
  if (authStore.refreshToken?.value) {
    // Teachers don't require 2FA, try direct login
    loading.value = true
    try {
      const result = await authStore.loginNo2FA()
      if (result.success) {
        message.success('Login successful')
        router.push('/teacher/courses')
      } else {
        // Clear invalid token
        authStore.setTokens(null, null)
      }
    } catch (error) {
      // Clear invalid token
      authStore.setTokens(null, null)
    } finally {
      loading.value = false
    }
  }
})

const handleLogin = async () => {
  loading.value = true
  try {
    const result = await authStore.login(loginForm.value.username, loginForm.value.password)
    if (result.success) {
      // Teachers typically don't require 2FA, login directly
      const loginResult = await authStore.loginNo2FA()
      if (loginResult.success) {
        message.success('Login successful')
        router.push('/teacher/courses')
      } else {
        message.error(loginResult.error || 'Login failed')
      }
    } else {
      message.error(result.error || 'Login failed')
    }
  } catch (error) {
    message.error(error.message || 'Login failed')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
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

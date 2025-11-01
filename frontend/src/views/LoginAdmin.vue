<template>
  <div class="login-container">
    <a-card class="login-card">
      <template #title>
        <div class="login-header">
          <CrownOutlined style="font-size: 24px; margin-right: 8px;" />
          <span>Administrator Login</span>
        </div>
      </template>
      
      <a-form
        :model="loginForm"
        @finish="handleLogin"
        layout="vertical"
      >
        <a-alert
          message="Administrator Access"
          description="This portal is for system administrators only."
          type="warning"
          show-icon
          style="margin-bottom: 16px"
        />

        <a-form-item
          label="Username"
          name="username"
          :rules="[{ required: true, message: 'Please input your username!' }]"
        >
          <a-input v-model:value="loginForm.username" placeholder="Admin Username" size="large" />
        </a-form-item>

        <a-form-item
          label="Password"
          name="password"
          :rules="[{ required: true, message: 'Please input your password!' }]"
        >
          <a-input-password v-model:value="loginForm.password" placeholder="Admin Password" size="large" />
        </a-form-item>

        <a-form-item>
          <a-button type="primary" html-type="submit" block :loading="loading" size="large">
            Login as Admin
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
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { CrownOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const authStore = useAuthStore()

const loginForm = ref({
  username: '',
  password: '',
})

const loading = ref(false)

const handleLogin = async () => {
  loading.value = true
  try {
    await authStore.adminLogin(loginForm.value.username, loginForm.value.password)
    message.success('Admin login successful')
    router.push('/admin/users')
  } catch (error) {
    message.error(error.message || 'Admin login failed')
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
  background: linear-gradient(135deg, #fbc2eb 0%, #a6c1ee 100%);
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

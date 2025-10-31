<template>
  <div class="login-container">
    <a-card class="login-card" title="Course Selection System">
      <a-tabs v-model:activeKey="activeTab">
        <!-- Student/Teacher Login -->
        <a-tab-pane key="user" tab="Student/Teacher Login">
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
              <a-input v-model:value="loginForm.username" placeholder="Username" />
            </a-form-item>

            <a-form-item
              label="Password"
              name="password"
              :rules="[{ required: true, message: 'Please input your password!' }]"
            >
              <a-input-password v-model:value="loginForm.password" placeholder="Password" />
            </a-form-item>

            <a-form-item>
              <a-button type="primary" html-type="submit" block :loading="loading">
                Login
              </a-button>
            </a-form-item>

            <a-form-item>
              <router-link to="/register">Don't have an account? Register</router-link>
            </a-form-item>
          </a-form>

          <!-- 2FA Verification -->
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
              :rules="[
                { required: true, message: 'Please input your 2FA code!' },
                { pattern: /^\d{6}$/, message: '2FA code must be 6 digits!' }
              ]"
            >
              <a-input
                v-model:value="twoFactorForm.totpCode"
                placeholder="000000"
                maxlength="6"
              />
            </a-form-item>

            <a-form-item>
              <a-space>
                <a-button type="primary" html-type="submit" :loading="loading">
                  Verify
                </a-button>
                <a-button @click="cancelTwoFactor">Cancel</a-button>
              </a-space>
            </a-form-item>
          </a-form>
        </a-tab-pane>

        <!-- Admin Login -->
        <a-tab-pane key="admin" tab="Admin Login">
          <a-form :model="adminForm" @finish="handleAdminLogin" layout="vertical">
            <a-form-item
              label="Admin Username"
              name="username"
              :rules="[{ required: true, message: 'Please input admin username!' }]"
            >
              <a-input v-model:value="adminForm.username" placeholder="Admin Username" />
            </a-form-item>

            <a-form-item
              label="Password"
              name="password"
              :rules="[{ required: true, message: 'Please input password!' }]"
            >
              <a-input-password v-model:value="adminForm.password" placeholder="Password" />
            </a-form-item>

            <a-form-item>
              <a-button type="primary" html-type="submit" block :loading="loading">
                Admin Login
              </a-button>
            </a-form-item>
          </a-form>
        </a-tab-pane>
      </a-tabs>
    </a-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/store/auth'
import authApi from '@/api/auth'

const router = useRouter()
const authStore = useAuthStore()

const activeTab = ref('user')
const loading = ref(false)
const needsTwoFactor = ref(false)

const loginForm = ref({
  username: '',
  password: '',
})

const twoFactorForm = ref({
  totpCode: '',
})

const adminForm = ref({
  username: '',
  password: '',
})

const handleLogin = async () => {
  loading.value = true
  try {
    const result = await authStore.login(loginForm.value.username, loginForm.value.password)
    if (result.success) {
      needsTwoFactor.value = true
      message.success('Please enter your 2FA code')
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
    const result = await authStore.verify2FA(twoFactorForm.value.totpCode)
    if (result.success) {
      message.success('Login successful!')
      // Redirect based on user type
      if (authStore.userType === 'student') {
        router.push('/student/courses')
      } else if (authStore.userType === 'teacher') {
        router.push('/teacher/courses')
      }
    } else {
      message.error(result.error || '2FA verification failed')
    }
  } catch (error) {
    message.error(error.message || '2FA verification failed')
  } finally {
    loading.value = false
  }
}

const cancelTwoFactor = () => {
  needsTwoFactor.value = false
  twoFactorForm.value.totpCode = ''
}

const handleAdminLogin = async () => {
  loading.value = true
  try {
    const response = await authApi.adminLogin(adminForm.value.username, adminForm.value.password)
    authStore.setTokens(response.access_token, null)
    
    // Fetch admin info
    const userInfo = await authApi.getUserInfo(response.access_token)
    authStore.setUser(userInfo)
    
    message.success('Admin login successful!')
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
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 100%;
  max-width: 450px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}
</style>

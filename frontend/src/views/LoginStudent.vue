<template>
  <div class="login-container">
    <a-card class="login-card">
      <template #title>
        <div class="login-header">
          <BookOutlined style="font-size: 24px; margin-right: 8px;" />
          <span>Student Login</span>
        </div>
      </template>
      
      <!-- Phase 1: Username & Password (only shown when no valid refresh token) -->
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
          <a-input 
            v-model:value="loginForm.username" 
            placeholder="Username" 
            size="large"
            autocomplete="username"
          />
        </a-form-item>

        <a-form-item
          label="Password"
          name="password"
          :rules="[{ required: true, message: 'Please input your password!' }]"
        >
          <a-input-password 
            v-model:value="loginForm.password" 
            placeholder="Password" 
            size="large"
            autocomplete="current-password"
          />
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

      <!-- Phase 2: 2FA Verification (shown when refresh token exists) -->
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
          <a-space direction="vertical" style="width: 100%">
            <a-button type="link" block @click="showResetModal">
              Reset 2FA
            </a-button>
            <a-button type="link" block @click="cancelTwoFactor">
              Cancel / Use Different Account
            </a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-card>

    <!-- 2FA Reset Modal -->
    <a-modal
      v-model:open="resetModalVisible"
      title="Reset 2FA"
      @ok="handleReset2FA"
      :confirmLoading="resetting"
    >
      <a-alert
        message="2FA Reset Process"
        description="To reset your 2FA, you need a reset code from an administrator and access to your new authenticator app."
        type="info"
        show-icon
        style="margin-bottom: 16px"
      />
      
      <a-form layout="vertical">
        <a-form-item label="Reset Code" required>
          <a-input
            v-model:value="resetForm.resetCode"
            placeholder="Enter 8-character reset code"
            maxlength="8"
            size="large"
          />
          <div style="margin-top: 4px; font-size: 12px; color: #888;">
            Request a reset code from your administrator
          </div>
        </a-form-item>

        <a-form-item label="New 2FA Code" required>
          <a-input
            v-model:value="resetForm.newTotpCode"
            placeholder="000000"
            maxlength="6"
            size="large"
          />
          <div style="margin-top: 4px; font-size: 12px; color: #888;">
            Enter the 6-digit code from your NEW authenticator app
          </div>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
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

const resetForm = ref({
  resetCode: '',
  newTotpCode: '',
})

const loading = ref(false)
const needsTwoFactor = ref(false)
const resetModalVisible = ref(false)
const resetting = ref(false)

// Check if we have a valid refresh token on mount
onMounted(async () => {
  if (authStore.refreshToken?.value) {
    // We have a refresh token, check 2FA status
    const statusResult = await authStore.check2FAStatus()
    
    if (statusResult.success) {
      if (statusResult.has_2fa) {
        // User has 2FA enabled, show 2FA screen
        needsTwoFactor.value = true
      } else {
        // Student without 2FA, login directly and redirect to setup
        loading.value = true
        try {
          const result = await authStore.loginNo2FA()
          if (result.success) {
            message.info('Please set up 2FA for your account')
            router.push('/student/setup-2fa')
          } else {
            message.error(result.error || 'Login failed')
            // Clear tokens and show login form
            authStore.setTokens(null, null)
            needsTwoFactor.value = false
          }
        } catch (error) {
          message.error(error.message || 'Login failed')
          authStore.setTokens(null, null)
          needsTwoFactor.value = false
        } finally {
          loading.value = false
        }
      }
    } else {
      // Invalid token or error, clear it and show login form
      authStore.setTokens(null, null)
      needsTwoFactor.value = false
    }
  }
})

const handleLogin = async () => {
  loading.value = true
  try {
    const result = await authStore.login(loginForm.value.username, loginForm.value.password)
    if (result.success) {
      // Check if user has 2FA enabled
      const statusResult = await authStore.check2FAStatus()
      
      if (statusResult.success && statusResult.has_2fa) {
        // 2FA is enabled, show 2FA screen
        needsTwoFactor.value = true
      } else {
        // Student without 2FA, login directly and redirect to setup
        const loginResult = await authStore.loginNo2FA()
        if (loginResult.success) {
          message.info('Please set up 2FA for your account')
          router.push('/student/setup-2fa')
        } else {
          message.error(loginResult.error || 'Login failed')
        }
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

const handleTwoFactor = async () => {
  loading.value = true
  try {
    // Sanitize to 6 digits
    const code = (twoFactorForm.value.totpCode || '').replace(/\D/g, '').slice(0, 6)
    if (code.length !== 6) {
      throw new Error('2FA code must be 6 digits')
    }
    await authStore.verify2FA(code)
    message.success('Login successful')
    router.push('/student/courses')
  } catch (error) {
    message.error(error.message || '2FA verification failed')
  } finally {
    loading.value = false
  }
}

const cancelTwoFactor = () => {
  // Clear tokens and return to username/password login
  authStore.setTokens(null, null)
  needsTwoFactor.value = false
  loginForm.value = { username: '', password: '' }
  twoFactorForm.value = { totpCode: '' }
}

const showResetModal = () => {
  resetModalVisible.value = true
  resetForm.value = { resetCode: '', newTotpCode: '' }
}

const handleReset2FA = async () => {
  if (!resetForm.value.resetCode || !resetForm.value.newTotpCode) {
    message.error('Please fill in all fields')
    return
  }

  if (resetForm.value.resetCode.length !== 8) {
    message.error('Reset code must be 8 characters')
    return
  }

  if (resetForm.value.newTotpCode.length !== 6) {
    message.error('2FA code must be 6 digits')
    return
  }

  resetting.value = true
  try {
    const result = await authStore.reset2FAWithCode(
      resetForm.value.resetCode,
      resetForm.value.newTotpCode
    )
    
    if (result.success) {
      message.success('2FA reset successful! Please login with your new 2FA code.')
      resetModalVisible.value = false
      // Clear current session and return to login
      authStore.setTokens(null, null)
      needsTwoFactor.value = false
      loginForm.value = { username: '', password: '' }
      twoFactorForm.value = { totpCode: '' }
    } else {
      message.error(result.error || '2FA reset failed')
    }
  } catch (error) {
    message.error(error.message || '2FA reset failed')
  } finally {
    resetting.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: cornflowerblue;
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

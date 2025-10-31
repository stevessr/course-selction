<template>
  <div class="register-container">
    <a-card class="register-card" title="Register">
      <a-form
        v-if="!needsTwoFactor"
        :model="registerForm"
        @finish="handleRegister"
        layout="vertical"
      >
        <a-form-item
          label="Username"
          name="username"
          :rules="[
            { required: true, message: 'Please input your username!' },
            { min: 3, message: 'Username must be at least 3 characters!' }
          ]"
        >
          <a-input v-model:value="registerForm.username" placeholder="Username" />
        </a-form-item>

        <a-form-item
          label="Password"
          name="password"
          :rules="[
            { required: true, message: 'Please input your password!' },
            { min: 6, message: 'Password must be at least 6 characters!' }
          ]"
        >
          <a-input-password v-model:value="registerForm.password" placeholder="Password" />
        </a-form-item>

        <a-form-item
          label="User Type"
          name="userType"
          :rules="[{ required: true, message: 'Please select user type!' }]"
        >
          <a-select v-model:value="registerForm.userType" placeholder="Select user type">
            <a-select-option value="student">Student</a-select-option>
            <a-select-option value="teacher">Teacher</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item
          label="Registration Code (Optional)"
          name="registrationCode"
        >
          <a-input
            v-model:value="registerForm.registrationCode"
            placeholder="Enter registration code if you have one"
          />
        </a-form-item>

        <a-form-item>
          <a-button type="primary" html-type="submit" block :loading="loading">
            Register
          </a-button>
        </a-form-item>

        <a-form-item>
          <router-link to="/login">Already have an account? Login</router-link>
        </a-form-item>
      </a-form>

      <!-- 2FA Setup -->
      <div v-else>
        <a-alert
          message="Two-Factor Authentication Setup"
          description="Scan the QR code with your authenticator app (Google Authenticator, Authy, etc.) and enter the 6-digit code to complete registration."
          type="info"
          show-icon
          style="margin-bottom: 16px"
        />

        <div class="qr-code-container">
          <canvas ref="qrCanvas"></canvas>
        </div>

        <a-alert
          type="warning"
          message="Important"
          description="Please save your secret key in a safe place. You will need it if you lose access to your authenticator app."
          show-icon
          style="margin: 16px 0"
        />

        <a-form :model="twoFactorForm" @finish="handleCompleteTwoFactor" layout="vertical">
          <a-form-item
            label="Secret Key"
            name="secret"
          >
            <a-input
              :value="authStore.totpSecret"
              readonly
              @click="copySecret"
            >
              <template #suffix>
                <CopyOutlined @click="copySecret" style="cursor: pointer" />
              </template>
            </a-input>
          </a-form-item>

          <a-form-item
            label="Verification Code"
            name="totpCode"
            :rules="[
              { required: true, message: 'Please input verification code!' },
              { pattern: /^\d{6}$/, message: 'Code must be 6 digits!' }
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
                Complete Registration
              </a-button>
              <a-button @click="cancelRegistration">Cancel</a-button>
            </a-space>
          </a-form-item>
        </a-form>
      </div>
    </a-card>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { CopyOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '@/store/auth'
import QRCode from 'qrcode'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const needsTwoFactor = ref(false)
const qrCanvas = ref(null)

const registerForm = ref({
  username: '',
  password: '',
  userType: 'student',
  registrationCode: '',
})

const twoFactorForm = ref({
  totpCode: '',
})

const handleRegister = async () => {
  loading.value = true
  try {
    const result = await authStore.register(
      registerForm.value.username,
      registerForm.value.password,
      registerForm.value.userType,
      registerForm.value.registrationCode || null
    )
    
    if (result.success) {
      needsTwoFactor.value = true
      message.success('Registration initiated. Please setup 2FA.')
      
      // Generate QR code
      await nextTick()
      if (qrCanvas.value && result.totpUri) {
        QRCode.toCanvas(qrCanvas.value, result.totpUri, { width: 250 })
      }
    } else {
      message.error(result.error || 'Registration failed')
    }
  } catch (error) {
    message.error(error.message || 'Registration failed')
  } finally {
    loading.value = false
  }
}

const handleCompleteTwoFactor = async () => {
  loading.value = true
  try {
    const result = await authStore.completeRegistration(twoFactorForm.value.totpCode)
    if (result.success) {
      message.success('Registration completed successfully!')
      // Redirect based on user type
      if (authStore.userType === 'student') {
        router.push('/student/courses')
      } else if (authStore.userType === 'teacher') {
        router.push('/teacher/courses')
      }
    } else {
      message.error(result.error || 'Verification failed')
    }
  } catch (error) {
    message.error(error.message || 'Verification failed')
  } finally {
    loading.value = false
  }
}

const copySecret = () => {
  navigator.clipboard.writeText(authStore.totpSecret)
  message.success('Secret key copied to clipboard')
}

const cancelRegistration = () => {
  router.push('/login')
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.register-card {
  width: 100%;
  max-width: 500px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.qr-code-container {
  display: flex;
  justify-content: center;
  padding: 20px;
  background: white;
  border-radius: 8px;
  margin-bottom: 16px;
}
</style>

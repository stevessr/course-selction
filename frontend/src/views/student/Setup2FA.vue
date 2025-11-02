<template>
  <div class="setup-2fa-container">
    <a-card class="setup-card">
      <template #title>
        <div class="setup-header">
          <SafetyOutlined style="font-size: 24px; margin-right: 8px;" />
          <span>设置双因素认证 / Setup Two-Factor Authentication</span>
        </div>
      </template>

      <a-alert
        v-if="!setupComplete"
        message="双因素认证设置 / Two-Factor Authentication Setup"
        description="扫描二维码或输入密钥到您的身份验证器应用（Google Authenticator、Authy等），然后输入6位数验证码完成设置。 / Scan the QR code or enter the secret key into your authenticator app (Google Authenticator, Authy, etc.), then enter the 6-digit code to complete setup."
        type="info"
        show-icon
        style="margin-bottom: 20px"
      />

      <div v-if="!setupComplete && totpSecret" class="setup-content">
        <div class="qr-code-container">
          <canvas ref="qrCanvas"></canvas>
        </div>

        <a-divider />

        <a-alert
          type="warning"
          message="重要 / Important"
          description="请将您的密钥保存在安全的地方。如果您失去对身份验证器应用的访问权限，您将需要它。 / Please save your secret key in a safe place. You will need it if you lose access to your authenticator app."
          show-icon
          style="margin-bottom: 16px"
        />

        <a-form :model="verifyForm" @finish="handleVerify" layout="vertical">
          <a-form-item label="密钥 / Secret Key">
            <a-input
              :value="totpSecret"
              readonly
              @click="copySecret"
            >
              <template #suffix>
                <CopyOutlined @click="copySecret" style="cursor: pointer" />
              </template>
            </a-input>
          </a-form-item>

          <a-form-item
            label="验证码 / Verification Code"
            name="totpCode"
            :rules="[
              { required: true, message: '请输入验证码 / Please input verification code!' },
              { len: 6, message: '验证码必须是6位数字 / Code must be 6 digits!' }
            ]"
          >
            <a-input
              v-model:value="verifyForm.totpCode"
              placeholder="000000"
              maxlength="6"
              size="large"
            />
          </a-form-item>

          <a-form-item>
            <a-space direction="vertical" style="width: 100%">
              <a-button type="primary" html-type="submit" block :loading="loading" size="large">
                验证并完成设置 / Verify and Complete Setup
              </a-button>
              <a-button block @click="handleCancel" size="large">
                取消 / Cancel
              </a-button>
            </a-space>
          </a-form-item>
        </a-form>
      </div>

      <div v-else-if="setupComplete" class="success-container">
        <a-result
          status="success"
          title="双因素认证设置成功！"
          sub-title="2FA Setup Successful! Please login again to access your account."
        >
          <template #extra>
            <a-button type="primary" size="large" @click="handleLoginRedirect">
              返回登录 / Back to Login
            </a-button>
          </template>
        </a-result>
      </div>

      <div v-if="loading && !totpSecret" style="text-align: center; padding: 40px;">
        <a-spin size="large" />
        <p style="margin-top: 16px;">正在生成密钥... / Generating secret key...</p>
      </div>
    </a-card>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { SafetyOutlined, CopyOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '@/store/auth'
import QRCode from 'qrcode'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const totpSecret = ref('')
const totpUri = ref('')
const setupComplete = ref(false)
const qrCanvas = ref(null)

const verifyForm = ref({
  totpCode: '',
})

// Generate 2FA secret on mount
onMounted(async () => {
  if (!authStore.refreshToken?.value) {
    message.error('请先登录 / Please login first')
    router.push('/login/student')
    return
  }

  loading.value = true
  try {
    const response = await fetch('/api/auth/setup/2fa/v1', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authStore.refreshToken.value}`,
      },
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to generate 2FA secret')
    }

    const data = await response.json()
    totpSecret.value = data.totp_secret
    totpUri.value = data.totp_uri

    // Generate QR code
    // Note: the canvas is inside a v-if block that depends on totpSecret,
    // so we must wait for the DOM to update before drawing to it.
    await nextTick()
    if (qrCanvas.value && totpUri.value) {
      try {
        await QRCode.toCanvas(qrCanvas.value, totpUri.value, {
          width: 250,
          margin: 2,
        })
      } catch (e) {
        console.error('Failed to render QR code:', e)
        message.error('二维码生成失败，请稍后重试 / Failed to render QR code')
      }
    }
  } catch (error) {
    message.error(error.message || '生成密钥失败 / Failed to generate secret')
    router.push('/login/student')
  } finally {
    loading.value = false
  }
})

const copySecret = () => {
  navigator.clipboard.writeText(totpSecret.value)
  message.success('密钥已复制 / Secret copied to clipboard')
}

const handleVerify = async () => {
  loading.value = true
  try {
    // Sanitize and validate TOTP code (digits only, length 6)
    const sanitized = (verifyForm.value.totpCode || '').replace(/\D/g, '').slice(0, 6)
    if (sanitized.length !== 6) {
      throw new Error('验证码必须是 6 位数字 / Code must be 6 digits!')
    }
    const response = await fetch('/api/auth/setup/2fa/v2', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authStore.refreshToken.value}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        totp_secret: totpSecret.value,
        totp_code: sanitized,
      }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Verification failed')
    }

    setupComplete.value = true
    message.success('双因素认证设置成功！/ 2FA Setup successful!')
    
    // Clear tokens to force re-login
    authStore.setTokens(null, null)
  } catch (error) {
    message.error(error.message || '验证失败 / Verification failed')
  } finally {
    loading.value = false
  }
}

const handleCancel = () => {
  authStore.logout()
  router.push('/login/student')
}

const handleLoginRedirect = () => {
  router.push('/login/student')
}
</script>

<style scoped>
.setup-2fa-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: cornflowerblue;
  padding: 20px;
}

.setup-card {
  width: 100%;
  max-width: 600px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.setup-header {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
}

.setup-content {
  padding: 20px 0;
}

.qr-code-container {
  display: flex;
  justify-content: center;
  padding: 20px;
  background: #f5f5f5;
  border-radius: 8px;
  margin-bottom: 20px;
}

.qr-code-container canvas {
  border-radius: 4px;
  background: white;
  padding: 10px;
}

.success-container {
  padding: 20px 0;
}
</style>

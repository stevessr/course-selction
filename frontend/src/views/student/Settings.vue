<template>
  <div class="settings-container">
    <a-card title="账户设置 / Account Settings">
      <!-- 2FA Required Alert for Students -->
      <a-alert
        v-if="!twoFAStatus.has_2fa"
        message="⚠️ 需要启用双因素认证 / 2FA Setup Required"
        description="为了保护您的账户安全，学生必须启用双因素认证才能访问选课系统。请完成以下设置。 / For account security, students must enable 2FA before accessing the course selection system. Please complete the setup below."
        type="warning"
        show-icon
        :closable="false"
        style="margin-bottom: 20px"
      />

      <a-tabs v-model:activeKey="activeTab">
        <!-- Password Change Tab -->
        <a-tab-pane key="password" tab="修改密码 / Change Password">
          <a-form
            :model="passwordForm"
            @finish="handlePasswordChange"
            layout="vertical"
            style="max-width: 500px"
          >
            <a-form-item
              label="当前密码 / Current Password"
              name="old_password"
              :rules="[{ required: true, message: '请输入当前密码' }]"
            >
              <a-input-password v-model:value="passwordForm.old_password" />
            </a-form-item>
            
            <a-form-item
              label="新密码 / New Password"
              name="new_password"
              :rules="[{ required: true, min: 6, message: '密码至少6位' }]"
            >
              <a-input-password v-model:value="passwordForm.new_password" />
            </a-form-item>
            
            <a-form-item
              label="确认新密码 / Confirm New Password"
              name="confirm_password"
              :rules="[
                { required: true, message: '请确认新密码' },
                { validator: validatePasswordMatch }
              ]"
            >
              <a-input-password v-model:value="passwordForm.confirm_password" />
            </a-form-item>
            
            <a-form-item>
              <a-button type="primary" html-type="submit" :loading="passwordLoading">
                修改密码 / Change Password
              </a-button>
            </a-form-item>
          </a-form>
        </a-tab-pane>

        <!-- 2FA Management Tab -->
        <a-tab-pane key="2fa" tab="双因素认证 / 2FA (必须)">
          <div v-if="twoFAStatus.has_2fa">
            <a-alert
              message="双因素认证已启用 / 2FA Enabled"
              description="您的账户已启用双因素认证保护"
              type="success"
              show-icon
              style="margin-bottom: 20px"
            />
            
            <a-form
              :model="disable2FAForm"
              @finish="handleDisable2FA"
              layout="vertical"
              style="max-width: 500px"
            >
              <a-form-item
                label="密码 / Password"
                name="password"
                :rules="[{ required: true, message: '请输入密码' }]"
              >
                <a-input-password v-model:value="disable2FAForm.password" />
              </a-form-item>
              
              <a-form-item
                label="2FA验证码 / 2FA Code"
                name="totp_code"
                :rules="[{ required: true, message: '请输入6位验证码' }]"
              >
                <a-input v-model:value="disable2FAForm.totp_code" placeholder="000000" maxlength="6" />
              </a-form-item>
              
              <a-form-item>
                <a-button type="danger" html-type="submit" :loading="disable2FALoading">
                  禁用2FA / Disable 2FA
                </a-button>
              </a-form-item>
            </a-form>
          </div>
          
          <div v-else>
            <a-alert
              message="⚠️ 双因素认证未启用 / 2FA Not Enabled (Required)"
              description="作为学生用户，您必须启用双因素认证才能使用选课系统。这是强制性的安全要求。 / As a student, you must enable 2FA to use the course selection system. This is a mandatory security requirement."
              type="error"
              show-icon
              style="margin-bottom: 20px"
            />
            
            <div v-if="!setup2FAData.qr_uri">
              <a-form
                :model="setup2FAForm"
                @finish="handleSetup2FA"
                layout="vertical"
                style="max-width: 500px"
              >
                <a-form-item
                  label="密码 / Password"
                  name="password"
                  :rules="[{ required: true, message: '请输入密码' }]"
                >
                  <a-input-password v-model:value="setup2FAForm.password" />
                </a-form-item>
                
                <a-form-item>
                  <a-button type="primary" html-type="submit" :loading="setup2FALoading">
                    开始设置2FA / Start 2FA Setup
                  </a-button>
                </a-form-item>
              </a-form>
            </div>
            
            <div v-else>
              <a-steps :current="1" style="margin-bottom: 20px">
                <a-step title="扫描二维码" description="Scan QR Code" />
                <a-step title="验证" description="Verify" />
              </a-steps>
              
              <div style="text-align: center; margin-bottom: 20px">
                <img :src="setup2FAData.qr_uri" alt="QR Code" style="max-width: 250px" />
                <p style="margin-top: 10px">
                  <a-tag>{{ setup2FAData.secret }}</a-tag>
                </p>
                <p class="text-muted">使用认证器应用扫描二维码或手动输入密钥</p>
              </div>
              
              <a-form
                :model="verify2FAForm"
                @finish="handleVerify2FA"
                layout="vertical"
                style="max-width: 500px; margin: 0 auto"
              >
                <a-form-item
                  label="验证码 / Verification Code"
                  name="totp_code"
                  :rules="[{ required: true, message: '请输入6位验证码' }]"
                >
                  <a-input v-model:value="verify2FAForm.totp_code" placeholder="000000" maxlength="6" />
                </a-form-item>
                
                <a-form-item>
                  <a-space>
                    <a-button type="primary" html-type="submit" :loading="verify2FALoading">
                      验证并启用 / Verify & Enable
                    </a-button>
                    <a-button @click="cancelSetup2FA">取消 / Cancel</a-button>
                  </a-space>
                </a-form-item>
              </a-form>
            </div>
          </div>
        </a-tab-pane>
      </a-tabs>
    </a-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { changePassword, setup2FA, verify2FA, disable2FA, get2FAStatus } from '@/api/auth'

const activeTab = ref('password')
const passwordLoading = ref(false)
const setup2FALoading = ref(false)
const verify2FALoading = ref(false)
const disable2FALoading = ref(false)

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const setup2FAForm = reactive({
  password: ''
})

const verify2FAForm = reactive({
  totp_code: ''
})

const disable2FAForm = reactive({
  password: '',
  totp_code: ''
})

const twoFAStatus = reactive({
  has_2fa: false
})

const setup2FAData = reactive({
  qr_uri: '',
  secret: ''
})

const validatePasswordMatch = async (rule, value) => {
  if (value !== passwordForm.new_password) {
    return Promise.reject('两次输入的密码不一致')
  }
  return Promise.resolve()
}

const handlePasswordChange = async () => {
  passwordLoading.value = true
  try {
    await changePassword({
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password
    })
    message.success('密码修改成功 / Password changed successfully')
    passwordForm.old_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
  } catch (error) {
    message.error(error.response?.data?.detail || '密码修改失败')
  } finally {
    passwordLoading.value = false
  }
}

const handleSetup2FA = async () => {
  setup2FALoading.value = true
  try {
    const response = await setup2FA({ password: setup2FAForm.password })
    setup2FAData.qr_uri = response.qr_uri
    setup2FAData.secret = response.secret
    message.success('请使用认证器应用扫描二维码')
  } catch (error) {
    message.error(error.response?.data?.detail || '2FA设置失败')
  } finally {
    setup2FALoading.value = false
  }
}

const handleVerify2FA = async () => {
  verify2FALoading.value = true
  try {
    await verify2FA({ totp_code: verify2FAForm.totp_code })
    message.success('2FA已成功启用！您现在可以使用选课系统了 / 2FA enabled successfully! You can now access the course selection system')
    twoFAStatus.has_2fa = true
    cancelSetup2FA()
    
    // Redirect to courses page after a short delay
    setTimeout(() => {
      window.location.href = '/student/courses'
    }, 2000)
  } catch (error) {
    message.error(error.response?.data?.detail || '验证码错误')
  } finally {
    verify2FALoading.value = false
  }
}

const handleDisable2FA = async () => {
  disable2FALoading.value = true
  try {
    await disable2FA({
      password: disable2FAForm.password,
      totp_code: disable2FAForm.totp_code
    })
    message.success('2FA已禁用 / 2FA disabled')
    twoFAStatus.has_2fa = false
    disable2FAForm.password = ''
    disable2FAForm.totp_code = ''
  } catch (error) {
    message.error(error.response?.data?.detail || '禁用失败')
  } finally {
    disable2FALoading.value = false
  }
}

const cancelSetup2FA = () => {
  setup2FAData.qr_uri = ''
  setup2FAData.secret = ''
  setup2FAForm.password = ''
  verify2FAForm.totp_code = ''
}

const load2FAStatus = async () => {
  try {
    const response = await get2FAStatus()
    twoFAStatus.has_2fa = response.has_2fa
    
    // Auto-switch to 2FA tab if not enabled (force students to set it up)
    if (!twoFAStatus.has_2fa) {
      activeTab.value = '2fa'
    }
  } catch (error) {
    console.error('Failed to load 2FA status:', error)
  }
}

onMounted(() => {
  load2FAStatus()
})
</script>

<style scoped>
.settings-container {
  padding: 24px;
}

.text-muted {
  color: #999;
  font-size: 14px;
}
</style>

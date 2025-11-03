<template>
  <div class="settings-container">
    <a-card :title="t('student.accountSettings')">
      <!-- 2FA Required Alert for Students -->
      <a-alert
        v-if="!twoFAStatus.has_2fa"
        :message="`⚠️ ${t('student.twoFASetupRequired')}`"
        :description="t('student.twoFASetupDesc')"
        type="warning"
        show-icon
        :closable="false"
        style="margin-bottom: 20px"
      />

      <a-tabs v-model:activeKey="activeTab">
        <!-- Password Change Tab -->
        <a-tab-pane key="password" :tab="t('student.changePassword')">
          <a-form
            :model="passwordForm"
            @finish="handlePasswordChange"
            layout="vertical"
            style="max-width: 500px"
          >
            <a-form-item
              :label="t('student.currentPassword')"
              name="old_password"
              :rules="[{ required: true, message: t('student.enterCurrentPassword') }]"
            >
              <a-input-password v-model:value="passwordForm.old_password" />
            </a-form-item>
            
            <a-form-item
              :label="t('student.newPassword')"
              name="new_password"
              :rules="[{ required: true, min: 6, message: t('student.passwordMinLength') }]"
            >
              <a-input-password v-model:value="passwordForm.new_password" />
            </a-form-item>
            
            <a-form-item
              :label="t('student.confirmPassword')"
              name="confirm_password"
              :rules="[
                { required: true, message: t('student.confirmNewPassword') },
                { validator: validatePasswordMatch }
              ]"
            >
              <a-input-password v-model:value="passwordForm.confirm_password" />
            </a-form-item>
            
            <a-form-item>
              <a-button type="primary" html-type="submit" :loading="passwordLoading">
                {{ t('student.changePassword') }}
              </a-button>
            </a-form-item>
          </a-form>
        </a-tab-pane>

        <!-- 2FA Management Tab -->
        <a-tab-pane key="2fa" :tab="`${t('student.twoFactorAuth')} ${t('student.twoFARequired')}`">
          <div v-if="twoFAStatus.has_2fa">
            <a-alert
              :message="t('student.twoFAEnabled')"
              :description="t('student.twoFAEnabledDesc')"
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
                :label="t('user.password')"
                name="password"
                :rules="[{ required: true, message: t('student.enterPassword') }]"
              >
                <a-input-password v-model:value="disable2FAForm.password" />
              </a-form-item>
              
              <a-form-item
                :label="t('student.verificationCode')"
                name="totp_code"
                :rules="[{ required: true, message: t('student.enter2FACode') }]"
              >
                <a-input v-model:value="disable2FAForm.totp_code" placeholder="000000" maxlength="6" />
              </a-form-item>
              
              <a-form-item>
                <a-button type="danger" html-type="submit" :loading="disable2FALoading">
                  {{ t('student.disable2FA') }}
                </a-button>
              </a-form-item>
            </a-form>
          </div>
          
          <div v-else>
            <a-alert
              :message="`⚠️ ${t('student.twoFANotEnabled')} ${t('student.twoFARequired')}`"
              :description="t('student.twoFAMandatoryDesc')"
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
                  :label="t('user.password')"
                  name="password"
                  :rules="[{ required: true, message: t('student.enterPassword') }]"
                >
                  <a-input-password v-model:value="setup2FAForm.password" />
                </a-form-item>
                
                <a-form-item>
                  <a-button type="primary" html-type="submit" :loading="setup2FALoading">
                    {{ t('student.start2FASetup') }}
                  </a-button>
                </a-form-item>
              </a-form>
            </div>
            
            <div v-else>
              <a-steps :current="1" style="margin-bottom: 20px">
                <a-step :title="t('student.scanQRCode')" />
                <a-step :title="t('student.verify')" />
              </a-steps>
              
              <div style="text-align: center; margin-bottom: 20px">
                <img :src="setup2FAData.qr_uri" alt="QR Code" style="max-width: 250px" />
                <p style="margin-top: 10px">
                  <a-tag>{{ setup2FAData.secret }}</a-tag>
                </p>
                <p class="text-muted">{{ t('student.scanQRCodeHint') }}</p>
              </div>
              
              <a-form
                :model="verify2FAForm"
                @finish="handleVerify2FA"
                layout="vertical"
                style="max-width: 500px; margin: 0 auto"
              >
                <a-form-item
                  :label="t('student.verificationCode')"
                  name="totp_code"
                  :rules="[{ required: true, message: t('student.enter2FACode') }]"
                >
                  <a-input v-model:value="verify2FAForm.totp_code" placeholder="000000" maxlength="6" />
                </a-form-item>
                
                <a-form-item>
                  <a-space>
                    <a-button type="primary" html-type="submit" :loading="verify2FALoading">
                      {{ t('student.verifyAndEnable') }}
                    </a-button>
                    <a-button @click="cancelSetup2FA">{{ t('common.cancel') }}</a-button>
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
import { useI18n } from 'vue-i18n'
import { changePassword, setup2FA, verify2FA, disable2FA, get2FAStatus } from '@/api/auth'
import { useAuthStore } from '@/store/auth'

const { t } = useI18n()
const authStore = useAuthStore()

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
    return Promise.reject(t('student.passwordNotMatch'))
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
    message.success(t('student.passwordChangeSuccess'))
    passwordForm.old_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
  } catch (error) {
    message.error(error.response?.data?.detail || t('student.passwordChangeFailed'))
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
    message.success(t('student.use2FAApp'))
  } catch (error) {
    message.error(error.response?.data?.detail || t('student.passwordChangeFailed'))
  } finally {
    setup2FALoading.value = false
  }
}

const handleVerify2FA = async () => {
  verify2FALoading.value = true
  try {
    await verify2FA({ totp_code: verify2FAForm.totp_code })
    message.success(t('student.twoFAEnableSuccess'))
    twoFAStatus.has_2fa = true
    cancelSetup2FA()
    
    // Redirect to courses page after a short delay
    setTimeout(() => {
      window.location.href = '/student/courses'
    }, 2000)
  } catch (error) {
    message.error(error.response?.data?.detail || t('student.verificationFailed'))
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
    message.success(t('student.twoFADisabled'))
    twoFAStatus.has_2fa = false
    disable2FAForm.password = ''
    disable2FAForm.totp_code = ''
  } catch (error) {
    message.error(error.response?.data?.detail || t('student.disableFailed'))
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
    const response = await get2FAStatus(authStore.accessToken?.value || authStore.accessToken)
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

<template>
  <div>
    <h1>Generate Registration Codes</h1>
    
    <a-card style="max-width: 600px; margin-bottom: 24px">
      <a-form :model="form" @finish="generateCode" layout="vertical">
        <a-form-item label="User Type" name="userType" :rules="[{ required: true }]">
          <a-select v-model:value="form.userType">
            <a-select-option value="student">Student</a-select-option>
            <a-select-option value="teacher">Teacher</a-select-option>
          </a-select>
        </a-form-item>
        
        <a-form-item label="Expires in (days)" name="expiresDays">
          <a-input-number v-model:value="form.expiresDays" :min="1" :max="365" style="width: 100%" />
        </a-form-item>
        
        <a-form-item>
          <a-button type="primary" html-type="submit" :loading="loading">
            Generate Code
          </a-button>
        </a-form-item>
      </a-form>
      
      <a-alert
        v-if="generatedCode"
        type="success"
        :message="`Registration Code Generated: ${generatedCode}`"
        show-icon
        style="margin-top: 16px"
      >
        <template #description>
          <p>Expires: {{ generatedExpiry }}</p>
          <a-button size="small" @click="copyCode">Copy Code</a-button>
        </template>
      </a-alert>
    </a-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/store/auth'
import authApi from '@/api/auth'

const authStore = useAuthStore()
const loading = ref(false)
const generatedCode = ref('')
const generatedExpiry = ref('')

const form = ref({
  userType: 'student',
  expiresDays: 7,
})

const generateCode = async () => {
  loading.value = true
  try {
    const response = await authApi.generateRegistrationCode(
      authStore.accessToken,
      form.value.userType,
      form.value.expiresDays
    )
    generatedCode.value = response.code
    generatedExpiry.value = new Date(response.expires_at).toLocaleString()
    message.success('Registration code generated successfully')
  } catch (error) {
    message.error(error.message || 'Failed to generate code')
  } finally {
    loading.value = false
  }
}

const copyCode = () => {
  navigator.clipboard.writeText(generatedCode.value)
  message.success('Code copied to clipboard')
}
</script>

<template>
  <div>
    <h1>Generate Registration Codes / 生成注册码</h1>
    
    <a-card style="max-width: 800px; margin-bottom: 24px">
      <a-form :model="form" @finish="generateCode" layout="vertical">
        <a-form-item label="User Type / 用户类型" name="userType" :rules="[{ required: true }]">
          <a-select v-model:value="form.userType">
            <a-select-option value="student">Student / 学生</a-select-option>
            <a-select-option value="teacher">Teacher / 教师</a-select-option>
          </a-select>
        </a-form-item>
        
        <a-form-item label="Expires in (days) / 有效期（天）" name="expiresDays">
          <a-input-number v-model:value="form.expiresDays" :min="1" :max="365" style="width: 100%" />
        </a-form-item>

        <a-form-item label="Number of Codes / 生成数量" name="count">
          <a-input-number v-model:value="form.count" :min="1" :max="100" style="width: 100%" />
          <div style="font-size: 12px; color: #888; margin-top: 4px;">
            Generate multiple codes at once (max 100) / 一次生成多个代码（最多100个）
          </div>
        </a-form-item>

        <a-form-item label="Tags / 标签" name="codeTags">
          <a-select 
            v-model:value="form.codeTags" 
            mode="tags" 
            placeholder="Add tags (students using these codes will get these tags) / 添加标签（使用这些代码的学生将自动获得这些标签）"
            style="width: 100%"
          >
          </a-select>
          <div style="font-size: 12px; color: #888; margin-top: 4px;">
            Students registering with this code will automatically receive these tags / 使用此代码注册的学生将自动获得这些标签
          </div>
        </a-form-item>
        
        <a-form-item>
          <a-button type="primary" html-type="submit" :loading="loading">
            Generate Code(s) / 生成注册码
          </a-button>
        </a-form-item>
      </a-form>
      
      <div v-if="generatedCodes.length > 0" style="margin-top: 24px;">
        <a-alert
          type="success"
          :message="`${generatedCodes.length} Registration Code(s) Generated / 已生成 ${generatedCodes.length} 个注册码`"
          show-icon
          style="margin-bottom: 16px"
        />

        <a-space direction="vertical" style="width: 100%">
          <div>
            <a-button @click="copyAllCodes" size="small">
              Copy All Codes / 复制所有代码
            </a-button>
            <a-button @click="exportCodes" size="small" style="margin-left: 8px;">
              Export as CSV / 导出为CSV
            </a-button>
          </div>

          <a-table
            :columns="codeColumns"
            :data-source="generatedCodes"
            :pagination="false"
            size="small"
            style="margin-top: 8px;"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'code'">
                <a-typography-text :copyable="{ text: record.code }">
                  <code>{{ record.code }}</code>
                </a-typography-text>
              </template>
              <template v-else-if="column.key === 'tags'">
                <a-tag v-for="tag in record.code_tags" :key="tag" color="green">
                  {{ tag }}
                </a-tag>
                <span v-if="!record.code_tags || record.code_tags.length === 0" style="color: #999;">无标签</span>
              </template>
              <template v-else-if="column.key === 'expires_at'">
                {{ new Date(record.expires_at).toLocaleString() }}
              </template>
            </template>
          </a-table>
        </a-space>
      </div>
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
const generatedCodes = ref([])

const form = ref({
  userType: 'student',
  expiresDays: 7,
  count: 1,
  codeTags: [],
})

const codeColumns = [
  {
    title: 'Code / 代码',
    dataIndex: 'code',
    key: 'code',
  },
  {
    title: 'Type / 类型',
    dataIndex: 'user_type',
    key: 'user_type',
  },
  {
    title: 'Tags / 标签',
    key: 'tags',
  },
  {
    title: 'Expires / 过期时间',
    key: 'expires_at',
  },
]

const generateCode = async () => {
  loading.value = true
  try {
    const response = await authApi.generateRegistrationCode(
      authStore.accessToken?.value || authStore.accessToken,
      form.value.userType,
      form.value.expiresDays,
      form.value.codeTags,
      form.value.count
    )
    
    // Handle both single and bulk response
    if (response.codes) {
      // Bulk generation
      generatedCodes.value = response.codes
      message.success(`Successfully generated ${response.count} registration code(s)`)
    } else {
      // Single code generation
      generatedCodes.value = [response]
      message.success('Registration code generated successfully')
    }
  } catch (error) {
    message.error(error.message || 'Failed to generate code')
  } finally {
    loading.value = false
  }
}

const copyAllCodes = () => {
  const codes = generatedCodes.value.map(c => c.code).join('\n')
  navigator.clipboard.writeText(codes)
  message.success('All codes copied to clipboard')
}

const exportCodes = () => {
  const headers = ['Code', 'User Type', 'Expires At', 'Tags']
  const rows = generatedCodes.value.map(c => [
    c.code,
    c.user_type,
    new Date(c.expires_at).toISOString(),
    (c.code_tags || []).join(';')
  ])

  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
  ].join('\n')

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `registration_codes_${new Date().toISOString().split('T')[0]}.csv`
  link.click()

  message.success('Codes exported to CSV')
}
</script>

<template>
  <div class="reset-codes-management">
    <a-card>
      <template #title>
        <div class="card-title">
          <h2>重置代码管理 / Reset Code Management</h2>
        </div>
      </template>

      <template #extra>
        <a-space>
          <a-button type="primary" @click="showGenerateModal">
            <template #icon><PlusOutlined /></template>
            生成重置代码
          </a-button>
          <a-button @click="loadCodes">
            <template #icon><ReloadOutlined /></template>
            刷新
          </a-button>
        </a-space>
      </template>

      <a-alert
        message="重置代码用途 / Reset Code Usage"
        description="重置代码允许学生在失去访问身份验证器应用时重置他们的双因素认证。请妥善保管并仅在必要时提供给学生。 / Reset codes allow students to reset their two-factor authentication when they lose access to their authenticator app. Keep them secure and only provide to students when necessary."
        type="info"
        show-icon
        style="margin-bottom: 20px"
      />

      <!-- Reset Codes Table -->
      <a-table
        :columns="columns"
        :data-source="codes"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
        row-key="id"
        class="codes-table"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'code'">
            <a-typography-text :copyable="{ text: record.code }">
              <code style="font-size: 14px;">{{ record.code }}</code>
            </a-typography-text>
          </template>

          <template v-else-if="column.key === 'username'">
            <a-tag color="blue">
              {{ record.username }}
            </a-tag>
          </template>

          <template v-else-if="column.key === 'is_used'">
            <a-badge
              :status="record.is_used ? 'error' : 'success'"
              :text="record.is_used ? '已使用' : '未使用'"
            />
          </template>

          <template v-else-if="column.key === 'expires_at'">
            <span :class="{ 'expired': isExpired(record.expires_at) }">
              {{ formatDate(record.expires_at) }}
              <a-tag v-if="isExpired(record.expires_at)" color="red">已过期</a-tag>
            </span>
          </template>

          <template v-else-if="column.key === 'created_at'">
            {{ formatDate(record.created_at) }}
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- Generate Reset Code Modal -->
    <a-modal
      v-model:open="generateModalVisible"
      title="生成重置代码 / Generate Reset Code"
      @ok="handleGenerateCode"
      @cancel="resetGenerateForm"
      :confirm-loading="generateLoading"
    >
      <a-form
        :model="generateForm"
        :label-col="{ span: 8 }"
        :wrapper-col="{ span: 16 }"
      >
        <a-form-item label="学生用户名 / Student Username" required>
          <a-input v-model:value="generateForm.username" placeholder="输入学生用户名 / Enter student username" />
        </a-form-item>

        <a-form-item label="有效期（天）/ Expiry (Days)" required>
          <a-input-number
            v-model:value="generateForm.expires_days"
            :min="1"
            :max="365"
            style="width: 100%"
            placeholder="默认7天 / Default 7 days"
          />
        </a-form-item>

        <a-alert
          message="提示 / Note"
          description="生成后请立即复制代码并提供给学生。代码仅显示一次。 / Please copy the code immediately after generation and provide it to the student. The code is only shown once."
          type="warning"
          show-icon
          style="margin-top: 10px"
        />
      </a-form>
    </a-modal>

    <!-- Generated Code Display Modal -->
    <a-modal
      v-model:open="codeDisplayModalVisible"
      title="重置代码已生成 / Reset Code Generated"
      :footer="null"
      width="600px"
    >
      <a-result
        status="success"
        title="重置代码生成成功！"
        sub-title="Reset Code Generated Successfully!"
      >
        <template #extra>
          <div class="code-display">
            <a-alert
              message="请立即复制此代码 / Please Copy This Code Immediately"
              type="warning"
              show-icon
              style="margin-bottom: 20px"
            />
            <div class="code-box">
              <a-typography-text :copyable="{ text: generatedCode }">
                <h1 style="font-family: monospace; letter-spacing: 2px;">{{ generatedCode }}</h1>
              </a-typography-text>
            </div>
            <a-descriptions bordered :column="1" style="margin-top: 20px;">
              <a-descriptions-item label="学生 / Student">
                {{ generatedUsername }}
              </a-descriptions-item>
              <a-descriptions-item label="过期时间 / Expires At">
                {{ formatDate(generatedExpiresAt) }}
              </a-descriptions-item>
            </a-descriptions>
            <a-button type="primary" block size="large" @click="closeCodeDisplay" style="margin-top: 20px;">
              关闭 / Close
            </a-button>
          </div>
        </template>
      </a-result>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/store/auth'
import api from '@/api/request'
import {
  PlusOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue'

const authStore = useAuthStore()

// State
const loading = ref(false)
const codes = ref([])

// Pagination
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showTotal: (total) => `共 ${total} 个代码`,
})

// Generate Modal
const generateModalVisible = ref(false)
const generateLoading = ref(false)
const generateForm = reactive({
  username: '',
  expires_days: 7,
})

// Code Display Modal
const codeDisplayModalVisible = ref(false)
const generatedCode = ref('')
const generatedUsername = ref('')
const generatedExpiresAt = ref('')

// Table columns
const columns = [
  {
    title: '代码 / Code',
    dataIndex: 'code',
    key: 'code',
    width: '20%',
  },
  {
    title: '学生 / Student',
    dataIndex: 'username',
    key: 'username',
    width: '15%',
  },
  {
    title: '状态 / Status',
    dataIndex: 'is_used',
    key: 'is_used',
    width: '12%',
  },
  {
    title: '过期时间 / Expires At',
    dataIndex: 'expires_at',
    key: 'expires_at',
    width: '20%',
  },
  {
    title: '创建时间 / Created At',
    dataIndex: 'created_at',
    key: 'created_at',
    width: '20%',
  },
]

// Methods
const loadCodes = async () => {
  loading.value = true
  try {
    // Note: This endpoint doesn't exist yet - we'd need to add it to the backend
    const response = await api.get('/auth/admin/reset-codes', {
      params: {
        page: pagination.current,
        page_size: pagination.pageSize,
      },
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    codes.value = response.codes || []
    pagination.total = response.total || 0
  } catch (error) {
    // For now, show empty list if endpoint doesn't exist
    codes.value = []
    pagination.total = 0
  } finally {
    loading.value = false
  }
}

const handleTableChange = (pag) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  loadCodes()
}

const showGenerateModal = () => {
  generateModalVisible.value = true
}

const resetGenerateForm = () => {
  Object.assign(generateForm, {
    username: '',
    expires_days: 7,
  })
  generateModalVisible.value = false
}

const handleGenerateCode = async () => {
  if (!generateForm.username) {
    message.error('请输入学生用户名 / Please enter student username')
    return
  }

  generateLoading.value = true
  try {
    const response = await api.post('/auth/generate/reset-code', {
      username: generateForm.username,
      expires_days: generateForm.expires_days,
    }, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })

    generatedCode.value = response.code
    generatedUsername.value = response.username
    generatedExpiresAt.value = response.expires_at

    message.success('重置代码生成成功！/ Reset code generated successfully!')
    resetGenerateForm()
    codeDisplayModalVisible.value = true
    loadCodes()
  } catch (error) {
    const errorDetail = error.response?.data?.detail || error.message
    if (error.response?.status === 401 || errorDetail?.includes('Invalid token')) {
      message.error('登录已过期，请重新登录 / Login expired, please login again')
      authStore.logout()
    } else {
      message.error('生成重置代码失败 / Failed to generate reset code: ' + errorDetail)
    }
  } finally {
    generateLoading.value = false
  }
}

const closeCodeDisplay = () => {
  codeDisplayModalVisible.value = false
  generatedCode.value = ''
  generatedUsername.value = ''
  generatedExpiresAt.value = ''
}

const isExpired = (dateString) => {
  if (!dateString) return false
  return new Date(dateString) < new Date()
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// Lifecycle
onMounted(() => {
  loadCodes()
})
</script>

<style scoped>
.reset-codes-management {
  padding: 24px;
}

.card-title h2 {
  margin: 0;
  font-size: 20px;
}

.codes-table {
  margin-top: 16px;
}

.expired {
  color: #ff4d4f;
}

.code-display {
  padding: 20px;
}

.code-box {
  background: #f5f5f5;
  padding: 30px;
  border-radius: 8px;
  text-align: center;
  border: 2px dashed #d9d9d9;
}

.code-box h1 {
  margin: 0;
  color: #1890ff;
}
</style>

<template>
  <div class="users-management">
    <a-card>
      <template #title>
        <div class="card-title">
          <h2>用户管理 / User Management</h2>
        </div>
      </template>

      <template #extra>
        <a-space>
          <a-button type="primary" @click="showAddUserModal">
            <template #icon><PlusOutlined /></template>
            添加用户
          </a-button>
          <a-button @click="showImportModal">
            <template #icon><UploadOutlined /></template>
            批量导入
          </a-button>
          <a-button @click="loadUsers">
            <template #icon><ReloadOutlined /></template>
            刷新
          </a-button>
        </a-space>
      </template>

      <!-- Search and Filter -->
      <div class="search-section">
        <a-row :gutter="16">
          <a-col :span="8">
            <a-input-search
              v-model:value="searchText"
              placeholder="搜索用户名"
              @search="handleSearch"
              allow-clear
            >
              <template #prefix><SearchOutlined /></template>
            </a-input-search>
          </a-col>
          <a-col :span="6">
            <a-select
              v-model:value="filterUserType"
              placeholder="用户类型"
              style="width: 100%"
              @change="handleSearch"
              allow-clear
            >
              <a-select-option value="student">学生</a-select-option>
              <a-select-option value="teacher">教师</a-select-option>
              <a-select-option value="admin">管理员</a-select-option>
            </a-select>
          </a-col>
        </a-row>
      </div>

      <!-- Users Table -->
      <a-table
        :columns="columns"
        :data-source="users"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
        row-key="user_id"
        class="users-table"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'username'">
            <a-space>
              <a-avatar :style="{ backgroundColor: getUserTypeColor(record.user_type) }">
                {{ record.username.charAt(0).toUpperCase() }}
              </a-avatar>
              <span class="username-text">{{ record.username }}</span>
            </a-space>
          </template>

          <template v-else-if="column.key === 'user_type'">
            <a-tag :color="getUserTypeTagColor(record.user_type)">
              {{ getUserTypeLabel(record.user_type) }}
            </a-tag>
          </template>

          <template v-else-if="column.key === 'is_active'">
            <a-badge
              :status="record.is_active ? 'success' : 'error'"
              :text="record.is_active ? '活跃' : '已停用'"
            />
          </template>

          <template v-else-if="column.key === 'has_2fa'">
            <a-tag v-if="record.user_type === 'student' || record.user_type === 'teacher'" :color="record.totp_secret ? 'green' : 'orange'">
              {{ record.totp_secret ? '已启用' : '未启用' }}
            </a-tag>
            <span v-else>-</span>
          </template>

          <template v-else-if="column.key === 'created_at'">
            {{ formatDate(record.created_at) }}
          </template>

          <template v-else-if="column.key === 'actions'">
            <a-space>
              <a-tooltip title="查看详情">
                <a-button size="small" @click="viewUserDetails(record)">
                  <template #icon><EyeOutlined /></template>
                </a-button>
              </a-tooltip>

              <a-tooltip 
                v-if="(record.user_type === 'student' || record.user_type === 'teacher') && record.totp_secret" 
                title="重置2FA">
                <a-button size="small" @click="reset2FA(record)">
                  <template #icon><KeyOutlined /></template>
                </a-button>
              </a-tooltip>

              <a-tooltip :title="record.is_active ? '停用' : '启用'">
                <a-button
                  size="small"
                  :type="record.is_active ? 'default' : 'primary'"
                  @click="toggleUserStatus(record)"
                >
                  <template #icon>
                    <StopOutlined v-if="record.is_active" />
                    <CheckCircleOutlined v-else />
                  </template>
                </a-button>
              </a-tooltip>

              <a-popconfirm
                title="确定要删除此用户吗？"
                ok-text="删除"
                cancel-text="取消"
                @confirm="deleteUser(record)"
              >
                <a-tooltip title="删除">
                  <a-button size="small" danger>
                    <template #icon><DeleteOutlined /></template>
                  </a-button>
                </a-tooltip>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- Add User Modal -->
    <a-modal
      v-model:open="addUserModalVisible"
      title="添加用户"
      @ok="handleAddUser"
      @cancel="resetAddUserForm"
      :confirm-loading="addUserLoading"
    >
      <a-form
        :model="newUser"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 18 }"
      >
        <a-form-item label="用户名" required>
          <a-input v-model:value="newUser.username" placeholder="输入用户名" />
        </a-form-item>

        <a-form-item label="用户类型" required>
          <a-select v-model:value="newUser.user_type" placeholder="选择类型">
            <a-select-option value="student">学生</a-select-option>
            <a-select-option value="teacher">教师</a-select-option>
            <a-select-option value="admin">管理员</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="密码">
          <a-input
            v-model:value="newUser.password"
            type="password"
            placeholder="留空自动生成"
          />
        </a-form-item>

        <a-form-item label="邮箱">
          <a-input v-model:value="newUser.email" type="email" placeholder="可选" />
        </a-form-item>

        <a-form-item label="姓名">
          <a-input v-model:value="newUser.name" placeholder="可选" />
        </a-form-item>

        <a-alert
          v-if="!newUser.password"
          message="将自动生成随机密码"
          type="info"
          show-icon
          style="margin-top: 10px"
        />
      </a-form>
    </a-modal>

    <!-- Import Users Modal -->
    <a-modal
      v-model:open="importModalVisible"
      title="批量导入用户"
      @ok="handleImportUsers"
      @cancel="resetImportForm"
      :confirm-loading="importLoading"
      width="600px"
    >
      <a-upload-dragger
        v-model:fileList="importFileList"
        :before-upload="beforeUpload"
        accept=".csv"
        :max-count="1"
      >
        <p class="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p class="ant-upload-text">点击或拖拽CSV文件到此区域上传</p>
        <p class="ant-upload-hint">
          支持CSV格式，包含字段：username, password, user_type, email, name
        </p>
      </a-upload-dragger>

      <a-divider />

      <div class="csv-example">
        <h4>CSV 格式示例:</h4>
        <pre>username,password,user_type,email,name
alice,pass123,student,alice@example.com,Alice Johnson
bob,pass456,teacher,bob@example.com,Bob Smith</pre>
      </div>
    </a-modal>

    <!-- User Details Modal -->
    <a-modal
      v-model:open="detailsModalVisible"
      title="用户详情"
      :footer="null"
      width="600px"
    >
      <a-descriptions v-if="selectedUser" bordered :column="1">
        <a-descriptions-item label="用户ID">
          {{ selectedUser.user_id || selectedUser.admin_id }}
        </a-descriptions-item>
        <a-descriptions-item label="用户名">
          {{ selectedUser.username }}
        </a-descriptions-item>
        <a-descriptions-item label="用户类型">
          <a-tag :color="getUserTypeTagColor(selectedUser.user_type)">
            {{ getUserTypeLabel(selectedUser.user_type) }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="状态">
          <a-badge
            :status="selectedUser.is_active ? 'success' : 'error'"
            :text="selectedUser.is_active ? '活跃' : '已停用'"
          />
        </a-descriptions-item>
        <a-descriptions-item v-if="selectedUser.user_type === 'student' || selectedUser.user_type === 'teacher'" label="2FA状态">
          <a-tag :color="selectedUser.totp_secret ? 'green' : 'orange'">
            {{ selectedUser.totp_secret ? '已启用' : '未启用' }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="创建时间">
          {{ formatDate(selectedUser.created_at) }}
        </a-descriptions-item>
        <a-descriptions-item v-if="selectedUser.updated_at" label="更新时间">
          {{ formatDate(selectedUser.updated_at) }}
        </a-descriptions-item>
      </a-descriptions>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/store/auth'
import adminApi from '@/api/admin'
import {
  PlusOutlined,
  UploadOutlined,
  ReloadOutlined,
  SearchOutlined,
  EyeOutlined,
  KeyOutlined,
  StopOutlined,
  CheckCircleOutlined,
  DeleteOutlined,
  InboxOutlined,
} from '@ant-design/icons-vue'

const authStore = useAuthStore()

// State
const loading = ref(false)
const users = ref([])
const searchText = ref('')
const filterUserType = ref(null)

// Pagination
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showTotal: (total) => `共 ${total} 个用户`,
})

// Add User Modal
const addUserModalVisible = ref(false)
const addUserLoading = ref(false)
const newUser = reactive({
  username: '',
  password: '',
  user_type: 'student',
  email: '',
  name: '',
})

// Import Modal
const importModalVisible = ref(false)
const importLoading = ref(false)
const importFileList = ref([])

// Details Modal
const detailsModalVisible = ref(false)
const selectedUser = ref(null)

// Table columns
const columns = [
  {
    title: '用户名',
    dataIndex: 'username',
    key: 'username',
    width: '20%',
  },
  {
    title: '类型',
    dataIndex: 'user_type',
    key: 'user_type',
    width: '12%',
  },
  {
    title: '状态',
    dataIndex: 'is_active',
    key: 'is_active',
    width: '12%',
  },
  {
    title: '2FA',
    key: 'has_2fa',
    width: '12%',
  },
  {
    title: '创建时间',
    dataIndex: 'created_at',
    key: 'created_at',
    width: '20%',
  },
  {
    title: '操作',
    key: 'actions',
    width: '24%',
  },
]

// Methods
const loadUsers = async () => {
  loading.value = true
  try {
    const response = await adminApi.listUsers(
      authStore.accessToken,
      filterUserType.value,
      pagination.current,
      pagination.pageSize,
      searchText.value
    )
    users.value = response.users || []
    pagination.total = response.total || 0
  } catch (error) {
    const errorDetail = error.response?.data?.detail || error.message;
    
    // Check if the error is due to invalid token
    if (error.response?.status === 401 || errorDetail?.includes('Invalid token')) {
      message.error('登录已过期，请重新登录');
      authStore.logout();
    } else {
      message.error('加载用户列表失败: ' + errorDetail)
    }
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.current = 1
  loadUsers()
}

const handleTableChange = (pag) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  loadUsers()
}

const showAddUserModal = () => {
  addUserModalVisible.value = true
}

const resetAddUserForm = () => {
  Object.assign(newUser, {
    username: '',
    password: '',
    user_type: 'student',
    email: '',
    name: '',
  })
  addUserModalVisible.value = false
}

const handleAddUser = async () => {
  if (!newUser.username || !newUser.user_type) {
    message.error('请填写必填项')
    return
  }

  addUserLoading.value = true
  try {
    await adminApi.addUser(authStore.accessToken, newUser)
    message.success('用户添加成功')
    resetAddUserForm()
    loadUsers()
  } catch (error) {
    const errorDetail = error.response?.data?.detail || error.message;
    
    // Check if the error is due to invalid token
    if (error.response?.status === 401 || errorDetail?.includes('Invalid token')) {
      message.error('登录已过期，请重新登录');
      authStore.logout();
    } else {
      message.error('添加用户失败: ' + errorDetail)
    }
  } finally {
    addUserLoading.value = false
  }
}

const showImportModal = () => {
  importModalVisible.value = true
}

const resetImportForm = () => {
  importFileList.value = []
  importModalVisible.value = false
}

const beforeUpload = () => {
  return false // Prevent auto upload
}

const handleImportUsers = async () => {
  if (importFileList.value.length === 0) {
    message.error('请选择CSV文件')
    return
  }

  const formData = new FormData()
  formData.append('file', importFileList.value[0].originFileObj)

  importLoading.value = true
  try {
    const response = await adminApi.importUsers(authStore.accessToken, formData)
    message.success(`成功导入 ${response.success_count} 个用户`)
    if (response.failed_count > 0) {
      message.warning(`${response.failed_count} 个用户导入失败`)
    }
    resetImportForm()
    loadUsers()
  } catch (error) {
    const errorDetail = error.response?.data?.detail || error.message;
    
    // Check if the error is due to invalid token
    if (error.response?.status === 401 || errorDetail?.includes('Invalid token')) {
      message.error('登录已过期，请重新登录');
      authStore.logout();
    } else {
      message.error('导入用户失败: ' + errorDetail)
    }
  } finally {
    importLoading.value = false
  }
}

const viewUserDetails = (user) => {
  selectedUser.value = user
  detailsModalVisible.value = true
}

const reset2FA = async (user) => {
  try {
    await adminApi.resetUser2FA(authStore.accessToken, user.username)
    message.success('2FA重置成功')
    loadUsers()
  } catch (error) {
    const errorDetail = error.response?.data?.detail || error.message;
    
    // Check if the error is due to invalid token
    if (error.response?.status === 401 || errorDetail?.includes('Invalid token')) {
      message.error('登录已过期，请重新登录');
      authStore.logout();
    } else {
      message.error('重置2FA失败: ' + errorDetail)
    }
  }
}

const toggleUserStatus = async (user) => {
  try {
    await adminApi.toggleUserStatus(authStore.accessToken, user.user_id, !user.is_active)
    message.success(`用户已${user.is_active ? '停用' : '启用'}`)
    loadUsers()
  } catch (error) {
    const errorDetail = error.response?.data?.detail || error.message;
    
    // Check if the error is due to invalid token
    if (error.response?.status === 401 || errorDetail?.includes('Invalid token')) {
      message.error('登录已过期，请重新登录');
      authStore.logout();
    } else {
      message.error('操作失败: ' + errorDetail)
    }
  }
}

const deleteUser = async (user) => {
  try {
    await adminApi.deleteUser(authStore.accessToken, user.user_id || user.admin_id, user.user_type)
    message.success('用户删除成功')
    loadUsers()
  } catch (error) {
    const errorDetail = error.response?.data?.detail || error.message;
    
    // Check if the error is due to invalid token
    if (error.response?.status === 401 || errorDetail?.includes('Invalid token')) {
      message.error('登录已过期，请重新登录');
      authStore.logout();
    } else {
      message.error('删除用户失败: ' + errorDetail)
    }
  }
}

// Utility functions
const getUserTypeColor = (type) => {
  const colors = {
    student: '#1890ff',
    teacher: '#52c41a',
    admin: '#722ed1',
  }
  return colors[type] || '#999'
}

const getUserTypeTagColor = (type) => {
  const colors = {
    student: 'blue',
    teacher: 'green',
    admin: 'purple',
  }
  return colors[type] || 'default'
}

const getUserTypeLabel = (type) => {
  const labels = {
    student: '学生',
    teacher: '教师',
    admin: '管理员',
  }
  return labels[type] || type
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// Lifecycle
onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.users-management {
  padding: 24px;
}

.card-title h2 {
  margin: 0;
  font-size: 20px;
}

.search-section {
  margin-bottom: 16px;
}

.username-text {
  font-weight: 500;
}

.users-table {
  margin-top: 16px;
}

.csv-example {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
}

.csv-example h4 {
  margin-top: 0;
}

.csv-example pre {
  background: white;
  padding: 8px;
  border-radius: 4px;
  font-size: 12px;
  overflow-x: auto;
}
</style>

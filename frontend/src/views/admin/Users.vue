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
          <a-button @click="exportUsers">
            <template #icon><DownloadOutlined /></template>
            导出用户
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

      <!-- Tabs for User Types -->
      <a-tabs v-model:activeKey="activeTab" @change="handleTabChange">
        <a-tab-pane key="all" tab="全部用户 / All Users">
          <!-- Search -->
          <div class="search-section">
            <a-input-search
              v-model:value="searchText"
              placeholder="搜索用户名 / Search username"
              @search="handleSearch"
              allow-clear
              style="width: 300px; margin-bottom: 16px;"
            >
              <template #prefix><SearchOutlined /></template>
            </a-input-search>
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

                  <a-tooltip v-if="record.user_type === 'student'" title="管理标签">
                    <a-button size="small" @click="showManageTagsModal(record)">
                      <template #icon><TagOutlined /></template>
                    </a-button>
                  </a-tooltip>

                  <a-tooltip 
                    v-if="(record.user_type === 'student' || record.user_type === 'teacher') && record.totp_secret" 
                    title="重置2FA">
                    <a-button size="small" @click="reset2FA(record)">
                      <template #icon><KeyOutlined /></template>
                    </a-button>
                  </a-tooltip>

                  <a-tooltip title="重置密码">
                    <a-button size="small" @click="showResetPasswordModal(record)">
                      <template #icon><LockOutlined /></template>
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
        </a-tab-pane>

        <a-tab-pane key="student" tab="学生 / Students">
          <!-- Search -->
          <div class="search-section">
            <a-input-search
              v-model:value="searchText"
              placeholder="搜索学生用户名 / Search student username"
              @search="handleSearch"
              allow-clear
              style="width: 300px; margin-bottom: 16px;"
            >
              <template #prefix><SearchOutlined /></template>
            </a-input-search>
          </div>

          <!-- Students Table -->
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
                <a-tag :color="record.totp_secret ? 'green' : 'orange'">
                  {{ record.totp_secret ? '已启用' : '未启用' }}
                </a-tag>
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

                  <a-tooltip title="管理标签">
                    <a-button size="small" @click="showManageTagsModal(record)">
                      <template #icon><TagOutlined /></template>
                    </a-button>
                  </a-tooltip>

                  <a-tooltip v-if="record.totp_secret" title="重置2FA">
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
                    title="确定要删除此学生吗？"
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
        </a-tab-pane>

        <a-tab-pane key="teacher" tab="教师 / Teachers">
          <!-- Search -->
          <div class="search-section">
            <a-input-search
              v-model:value="searchText"
              placeholder="搜索教师用户名 / Search teacher username"
              @search="handleSearch"
              allow-clear
              style="width: 300px; margin-bottom: 16px;"
            >
              <template #prefix><SearchOutlined /></template>
            </a-input-search>
          </div>

          <!-- Teachers Table -->
          <a-table
            :columns="columnsTeacher"
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
                    title="确定要删除此教师吗？"
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
        </a-tab-pane>

        <a-tab-pane key="admin" tab="管理员 / Administrators">
          <!-- Search -->
          <div class="search-section">
            <a-input-search
              v-model:value="searchText"
              placeholder="搜索管理员用户名 / Search admin username"
              @search="handleSearch"
              allow-clear
              style="width: 300px; margin-bottom: 16px;"
            >
              <template #prefix><SearchOutlined /></template>
            </a-input-search>
          </div>

          <!-- Admins Table -->
          <a-table
            :columns="columnsAdmin"
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

                  <a-popconfirm
                    title="确定要删除此管理员吗？"
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
        </a-tab-pane>
      </a-tabs>
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

    <!-- Manage Student Tags Modal -->
    <a-modal
      v-model:open="manageTagsModalVisible"
      title="管理学生标签"
      @ok="handleUpdateTags"
      @cancel="resetTagsForm"
      :confirm-loading="tagsLoading"
      width="600px"
    >
      <a-form
        :model="tagsForm"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 18 }"
      >
        <a-form-item label="学生">
          <a-input :value="selectedUser?.username" disabled />
        </a-form-item>

        <a-form-item label="标签">
          <a-select
            v-model:value="tagsForm.tags"
            mode="tags"
            placeholder="输入标签并按回车添加"
            style="width: 100%"
          >
          </a-select>
          <div style="margin-top: 8px; color: #666; font-size: 12px;">
            学生需要有匹配的标签才能选修带有标签要求的课程
          </div>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Reset Password Modal -->
    <a-modal
      v-model:open="resetPasswordModalVisible"
      title="重置用户密码 / Reset User Password"
      @cancel="closeResetPasswordModal"
      :footer="null"
      width="600px"
    >
      <a-form
        v-if="!newPasswordData"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 18 }"
      >
        <a-form-item label="用户名">
          <a-input :value="selectedUser?.username" disabled />
        </a-form-item>

        <a-form-item label="用户类型">
          <a-tag :color="getUserTypeTagColor(selectedUser?.user_type)">
            {{ getUserTypeLabel(selectedUser?.user_type) }}
          </a-tag>
        </a-form-item>

        <a-form-item label="密码设置方式">
          <a-radio-group v-model:value="passwordResetMode">
            <a-radio value="generate">自动生成随机密码</a-radio>
            <a-radio value="custom">手动设置密码</a-radio>
          </a-radio-group>
        </a-form-item>

        <a-form-item 
          v-if="passwordResetMode === 'custom'" 
          label="新密码"
          :rules="[{ required: true, min: 6, message: '密码至少6位' }]"
        >
          <a-input-password 
            v-model:value="customPassword" 
            placeholder="输入新密码（至少6位）" 
          />
        </a-form-item>

        <a-form-item 
          v-if="passwordResetMode === 'custom'" 
          label="确认密码"
          :rules="[{ required: true, message: '请确认密码' }]"
        >
          <a-input-password 
            v-model:value="confirmPassword" 
            placeholder="再次输入新密码" 
          />
        </a-form-item>

        <a-alert
          v-if="passwordResetMode === 'generate'"
          message="提示 / Note"
          description="将生成一个12位的随机密码。请将新密码安全地传递给用户。 / A 12-character random password will be generated. Please share it securely with the user."
          type="info"
          show-icon
          style="margin-bottom: 16px;"
        />

        <a-alert
          v-if="passwordResetMode === 'custom'"
          message="提示 / Note"
          description="请为用户设置一个安全的密码。密码至少需要6个字符。 / Please set a secure password for the user. Password must be at least 6 characters."
          type="info"
          show-icon
          style="margin-bottom: 16px;"
        />

        <div style="text-align: right;">
          <a-space>
            <a-button @click="closeResetPasswordModal">取消</a-button>
            <a-button type="primary" :loading="resetPasswordLoading" @click="resetPassword">
              {{ passwordResetMode === 'generate' ? '生成新密码' : '设置密码' }}
            </a-button>
          </a-space>
        </div>
      </a-form>

      <div v-else>
        <a-result
          status="success"
          title="密码重置成功 / Password Reset Successfully"
        >
          <template #subTitle>
            <div style="margin-bottom: 16px;">
              用户 <strong>{{ newPasswordData.username }}</strong> 的密码已{{ passwordResetMode === 'generate' ? '生成' : '设置' }}
            </div>
          </template>
          <template #extra>
            <a-card style="text-align: left;">
              <a-descriptions bordered :column="1">
                <a-descriptions-item label="新密码 / New Password">
                  <a-typography-text code copyable style="font-size: 16px; font-weight: bold;">
                    {{ newPasswordData.new_password }}
                  </a-typography-text>
                </a-descriptions-item>
              </a-descriptions>
              
              <div style="margin-top: 16px;">
                <a-alert
                  message="重要提示 / Important"
                  description="请立即复制新密码并安全地传递给用户。关闭此窗口后将无法再次查看密码。 / Please copy this password immediately and share it securely with the user. You won't be able to view it again after closing this window."
                  type="info"
                  show-icon
                />
              </div>

              <div style="text-align: right; margin-top: 16px;">
                <a-space>
                  <a-button @click="copyPassword">
                    <template #icon><CopyOutlined /></template>
                    复制密码
                  </a-button>
                  <a-button type="primary" @click="closeResetPasswordModal">
                    关闭
                  </a-button>
                </a-space>
              </div>
            </a-card>
          </template>
        </a-result>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/store/auth'
import adminApi from '@/api/admin'
import axios from 'axios'
import {
  PlusOutlined,
  UploadOutlined,
  ReloadOutlined,
  SearchOutlined,
  EyeOutlined,
  KeyOutlined,
  LockOutlined,
  CopyOutlined,
  StopOutlined,
  CheckCircleOutlined,
  DeleteOutlined,
  InboxOutlined,
  TagOutlined,
  DownloadOutlined,
} from '@ant-design/icons-vue'

const authStore = useAuthStore()

// State
const loading = ref(false)
const users = ref([])
const searchText = ref('')
const activeTab = ref('all')

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

// Manage Tags Modal
const manageTagsModalVisible = ref(false)
const tagsLoading = ref(false)
const tagsForm = reactive({
  tags: [],
})

// Reset Password Modal
const resetPasswordModalVisible = ref(false)
const resetPasswordLoading = ref(false)
const newPasswordData = ref(null)
const passwordResetMode = ref('generate') // 'generate' or 'custom'
const customPassword = ref('')
const confirmPassword = ref('')

// Table columns for all users
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

// Table columns for teachers (no 2FA column)
const columnsTeacher = [
  {
    title: '用户名',
    dataIndex: 'username',
    key: 'username',
    width: '25%',
  },
  {
    title: '类型',
    dataIndex: 'user_type',
    key: 'user_type',
    width: '15%',
  },
  {
    title: '状态',
    dataIndex: 'is_active',
    key: 'is_active',
    width: '15%',
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
    width: '25%',
  },
]

// Table columns for admins (no 2FA, no status column)
const columnsAdmin = [
  {
    title: '用户名',
    dataIndex: 'username',
    key: 'username',
    width: '30%',
  },
  {
    title: '类型',
    dataIndex: 'user_type',
    key: 'user_type',
    width: '20%',
  },
  {
    title: '创建时间',
    dataIndex: 'created_at',
    key: 'created_at',
    width: '30%',
  },
  {
    title: '操作',
    key: 'actions',
    width: '20%',
  },
]

// Methods
const getUserTypeFromTab = () => {
  if (activeTab.value === 'all') return null
  return activeTab.value
}

const handleTabChange = (key) => {
  activeTab.value = key
  pagination.current = 1
  searchText.value = ''
  loadUsers()
}

const loadUsers = async () => {
  loading.value = true
  try {
    const userType = getUserTypeFromTab()
    const response = await adminApi.listUsers(
      authStore.accessToken?.value || authStore.accessToken,
      userType,
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
  await adminApi.addUser(authStore.accessToken?.value || authStore.accessToken, newUser)
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
  const response = await adminApi.importUsers(authStore.accessToken?.value || authStore.accessToken, formData)
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
  await adminApi.resetUser2FA(authStore.accessToken?.value || authStore.accessToken, user.username)
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
  await adminApi.toggleUserStatus(authStore.accessToken?.value || authStore.accessToken, user.user_id, !user.is_active)
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
  await adminApi.deleteUser(authStore.accessToken?.value || authStore.accessToken, user.user_id || user.admin_id, user.user_type)
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

const showManageTagsModal = async (user) => {
  selectedUser.value = user
  // Initialize tags - we need to fetch from data node
  // For now, use empty array, but in production you'd fetch actual tags
  tagsForm.tags = []
  manageTagsModalVisible.value = true
}

const resetTagsForm = () => {
  tagsForm.tags = []
  manageTagsModalVisible.value = false
}

const handleUpdateTags = async () => {
  if (!selectedUser.value) {
    message.error('未选择用户')
    return
  }

  tagsLoading.value = true
  try {
    await adminApi.updateStudentTags(
      authStore.accessToken?.value || authStore.accessToken,
      selectedUser.value.user_id,
      tagsForm.tags
    )
    message.success('标签更新成功')
    resetTagsForm()
    loadUsers()
  } catch (error) {
    const errorDetail = error.response?.data?.detail || error.message;
    
    // Check if the error is due to invalid token
    if (error.response?.status === 401 || errorDetail?.includes('Invalid token')) {
      message.error('登录已过期，请重新登录');
      authStore.logout();
    } else {
      message.error('更新标签失败: ' + errorDetail)
    }
  } finally {
    tagsLoading.value = false
  }
}

// Reset Password
const showResetPasswordModal = (user) => {
  selectedUser.value = user
  newPasswordData.value = null
  passwordResetMode.value = 'generate'
  customPassword.value = ''
  confirmPassword.value = ''
  resetPasswordModalVisible.value = true
}

const resetPassword = async () => {
  // Validate custom password if in custom mode
  if (passwordResetMode.value === 'custom') {
    if (!customPassword.value || customPassword.value.length < 6) {
      message.error('密码至少需要6个字符')
      return
    }
    if (customPassword.value !== confirmPassword.value) {
      message.error('两次输入的密码不一致')
      return
    }
  }

  try {
    resetPasswordLoading.value = true
    const requestData = {
      username: selectedUser.value.username,
      user_type: selectedUser.value.user_type,
    }
    
    // Add custom password if in custom mode
    if (passwordResetMode.value === 'custom') {
      requestData.new_password = customPassword.value
    }

    const response = await axios.post(
      '/api/auth/admin/user/reset-password',
      requestData,
      {
        headers: {
          Authorization: `Bearer ${authStore.accessToken}`,
        },
      }
    )
    
    newPasswordData.value = response.data
    message.success('密码重置成功')
  } catch (error) {
    const errorDetail = error.response?.data?.detail || error.message
    
    if (error.response?.status === 401 || errorDetail?.includes('Invalid token')) {
      message.error('登录已过期，请重新登录')
      authStore.logout()
    } else {
      message.error('重置密码失败: ' + errorDetail)
    }
  } finally {
    resetPasswordLoading.value = false
  }
}

const copyPassword = () => {
  if (newPasswordData.value?.new_password) {
    navigator.clipboard.writeText(newPasswordData.value.new_password)
    message.success('密码已复制到剪贴板')
  }
}

const closeResetPasswordModal = () => {
  resetPasswordModalVisible.value = false
  selectedUser.value = null
  newPasswordData.value = null
  passwordResetMode.value = 'generate'
  customPassword.value = ''
  confirmPassword.value = ''
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

const exportUsers = () => {
  const usersToExport = users.value

  if (usersToExport.length === 0) {
    message.warning('没有可导出的用户')
    return
  }

  // Create CSV content
  const headers = ['User ID', 'Username', 'User Type', 'Is Active', 'Has 2FA', 'Tags', 'Created At']
  const rows = usersToExport.map(u => [
    u.user_id,
    u.username,
    u.user_type,
    u.is_active ? 'Yes' : 'No',
    u.has_2fa ? 'Yes' : 'No',
    (u.student_tags || []).join(';'),
    u.created_at || '',
  ])

  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
  ].join('\n')

  // Download file
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  const userTypeFilter = activeTab.value === 'all' ? 'all' : activeTab.value
  link.download = `users_${userTypeFilter}_${new Date().toISOString().split('T')[0]}.csv`
  link.click()

  message.success(`导出 ${usersToExport.length} 个用户成功`)
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

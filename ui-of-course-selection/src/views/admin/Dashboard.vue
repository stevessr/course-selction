<template>
  <a-layout-content style="padding: 24px; margin: 0; min-height: 280px">
    <a-page-header
      class="site-page-header"
      title="管理员控制面板"
      sub-title="Admin Dashboard"
    />

    <!-- Statistics Cards -->
    <a-row :gutter="[16, 16]" style="margin-bottom: 24px">
      <a-col :xs="24" :sm="24" :md="8">
        <a-card hoverable class="stat-card admin-card">
          <a-statistic
            title="管理员"
            :value="store.admins.length"
            prefix="👨‍💼"
            :value-style="{ color: '#667eea' }"
          />
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="24" :md="8">
        <a-card hoverable class="stat-card teacher-card">
          <a-statistic
            title="教师"
            :value="store.teachers.length"
            prefix="👨‍🏫"
            :value-style="{ color: '#f5576c' }"
          />
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="24" :md="8">
        <a-card hoverable class="stat-card student-card">
          <a-statistic
            title="学生"
            :value="store.students.length"
            prefix="👨‍🎓"
            :value-style="{ color: '#00f2fe' }"
          />
        </a-card>
      </a-col>
    </a-row>

    <!-- Loading State -->
    <a-spin v-if="store.loading && !store.error" size="large" style="width: 100%; text-align: center; padding: 50px 0" tip="加载中...">
    </a-spin>

    <!-- Error State -->
    <a-alert v-if="store.error" :message="store.error" type="error" show-icon style="margin-bottom: 24px" />

    <!-- Tab Navigation -->
    <a-tabs v-if="!store.loading || store.error" v-model:activeKey="activeTab">
      <a-tab-pane key="admins" tab="👨‍💼 管理员管理">
        <a-card title="管理员管理" :bordered="false">
          <template #extra>
            <a-button type="primary" @click="showAddAdminModal = true">
              <template #icon><plus-outlined /></template>
              添加管理员
            </a-button>
          </template>
          <a-table :columns="adminColumns" :data-source="store.admins" row-key="admin_id" :pagination="false">
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'actions'">
                <a-space>
                  <a-button @click="openResetPasswordModal(record.admin_name)">
                    <template #icon><key-outlined /></template>
                    重置密码
                  </a-button>
                  <a-popconfirm
                    title="确定要删除此管理员吗？"
                    ok-text="是"
                    cancel-text="否"
                    @confirm="handleDeleteAdmin(record.admin_name)"
                  >
                    <a-button type="danger" :disabled="record.admin_name === authStore.user?.user_name">
                      <template #icon><delete-outlined /></template>
                      删除
                    </a-button>
                  </a-popconfirm>
                </a-space>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-tab-pane>

      <a-tab-pane key="teachers" tab="👨‍🏫 教师管理">
        <a-card title="教师管理" :bordered="false">
          <template #extra>
            <a-button type="primary" @click="showAddTeacherModal = true">
              <template #icon><plus-outlined /></template>
              添加教师
            </a-button>
          </template>
          <a-table :columns="teacherColumns" :data-source="store.teachers" row-key="teacher_id" :pagination="false">
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'actions'">
                <a-space>
                  <a-button @click="openResetPasswordModal(record.teacher_name)">
                    <template #icon><key-outlined /></template>
                    重置密码
                  </a-button>
                  <a-button @click="openUpdateUserModal(record.teacher_name)">
                    <template #icon><edit-outlined /></template>
                    修改信息
                  </a-button>
                  <a-popconfirm
                    title="确定要删除此教师吗？"
                    ok-text="是"
                    cancel-text="否"
                    @confirm="handleDeleteTeacher(record.teacher_name)"
                  >
                    <a-button type="danger">
                      <template #icon><delete-outlined /></template>
                      删除
                    </a-button>
                  </a-popconfirm>
                </a-space>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-tab-pane>

      <a-tab-pane key="students" tab="👨‍🎓 学生管理">
        <a-card title="学生管理" :bordered="false">
          <template #extra>
            <a-space>
              <a-button type="primary" @click="showAddStudentModal = true">
                <template #icon><plus-outlined /></template>
                添加学生
              </a-button>
              <a-button @click="showBatchAddModal = true">
                <template #icon><upload-outlined /></template>
                批量添加
              </a-button>
            </a-space>
          </template>
          <a-table
            :columns="studentColumns"
            :data-source="store.students"
            row-key="student_id"
            :row-selection="{ selectedRowKeys: selectedStudents, onChange: onSelectChange }"
            :pagination="false"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'actions'">
                <a-space>
                  <a-button @click="openResetPasswordModal(record.student_name)">
                    <template #icon><key-outlined /></template>
                    重置密码
                  </a-button>
                  <a-button @click="openUpdateUserModal(record.student_name)">
                    <template #icon><edit-outlined /></template>
                    修改信息
                  </a-button>
                  <a-popconfirm
                    title="确定要删除此学生吗？"
                    ok-text="是"
                    cancel-text="否"
                    @confirm="handleDeleteStudent(record.student_name)"
                  >
                    <a-button type="danger">
                      <template #icon><delete-outlined /></template>
                      删除
                    </a-button>
                  </a-popconfirm>
                </a-space>
              </template>
            </template>
          </a-table>
          <a-button
            v-if="selectedStudents.length > 0"
            type="danger"
            @click="handleBatchDelete"
            style="margin-top: 16px"
          >
            <template #icon><delete-outlined /></template>
            批量删除 ({{ selectedStudents.length }})
          </a-button>
        </a-card>
      </a-tab-pane>

      <a-tab-pane key="credits" tab="🎫 Credit 管理">
        <a-card title="Credit 管理" :bordered="false">
          <template #extra>
            <a-button type="primary" @click="openCreditModal()">
              <template #icon><plus-outlined /></template>
              生成 Credits
            </a-button>
          </template>
          <a-alert
            message="关于 One-Time Credits"
            description="One-Time Credits 是用于修改 2FA 设置的一次性凭证。每个 Credit 使用 UUID 算法生成，全局唯一。任何用户都可以使用这些 Credits，但每个 Credit 只能使用一次。可以一次生成多个 Credits（最多 100 个）。"
            type="info"
            show-icon
            style="margin-bottom: 24px"
          />

          <a-space direction="vertical" v-if="isAdmin()">
            <a-button type="dashed" @click="showChange2faModal = true">
              <template #icon><key-outlined /></template>
              修改 2FA
            </a-button>
          </a-space>
        </a-card>
      </a-tab-pane>
    </a-tabs>

    <!-- Add Admin Modal -->
    <a-modal
      v-model:open="showAddAdminModal"
      title="添加管理员"
      @ok="handleAddAdmin"
      :confirm-loading="store.loading"
    >
      <a-form layout="vertical">
        <a-form-item label="用户名">
          <a-input v-model:value="newAdmin.name" placeholder="请输入管理员用户名" />
        </a-form-item>
        <a-form-item label="密码">
          <a-input-password v-model:value="newAdmin.password" placeholder="请输入密码" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Add Teacher Modal -->
    <a-modal
      v-model:open="showAddTeacherModal"
      title="添加教师"
      @ok="handleAddTeacher"
      :confirm-loading="store.loading"
    >
      <a-form layout="vertical">
        <a-form-item label="用户名">
          <a-input v-model:value="newTeacher.name" placeholder="请输入教师用户名" />
        </a-form-item>
        <a-form-item label="密码">
          <a-input-password v-model:value="newTeacher.password" placeholder="请输入密码" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Add Student Modal -->
    <a-modal
      v-model:open="showAddStudentModal"
      title="添加学生"
      @ok="handleAddStudent"
      :confirm-loading="store.loading"
    >
      <a-form layout="vertical">
        <a-form-item label="学号">
          <a-input-number v-model:value="newStudent.id" placeholder="请输入学号" style="width: 100%" />
        </a-form-item>
        <a-form-item label="用户名">
          <a-input v-model:value="newStudent.name" placeholder="请输入学生用户名" />
        </a-form-item>
        <a-form-item label="密码">
          <a-input-password v-model:value="newStudent.password" placeholder="请输入密码" />
        </a-form-item>
        <a-form-item label="类型">
          <a-select v-model:value="newStudent.type" style="width: 100%">
            <a-select-option value="undergraduate">本科生</a-select-option>
            <a-select-option value="graduate">研究生</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Batch Add Students Modal -->
    <a-modal
      v-model:open="showBatchAddModal"
      title="批量添加学生"
      @ok="handleBatchAdd"
      :confirm-loading="store.loading"
      width="700px"
    >
      <a-form layout="vertical">
        <a-form-item label="批量数据（JSON 格式）">
          <a-textarea
            v-model:value="batchStudentsJson"
            :rows="10"
            placeholder='[{"student_id": 2001, "student_name": "student1", "student_password": "password", "student_type": "undergraduate"}]'
          />
          <p class="help-text">
            格式示例：每个学生包含 student_id, student_name, student_password, student_type 字段
          </p>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Reset Password Modal -->
    <a-modal
      v-model:open="showResetPasswordModal"
      title="重置密码"
      @ok="handleResetPassword"
      :confirm-loading="store.loading"
    >
      <a-form layout="vertical">
        <a-form-item label="用户名">
          <a-input v-model:value="resetPasswordForm.userName" disabled />
        </a-form-item>
        <a-form-item label="新密码">
          <a-input-password v-model:value="resetPasswordForm.newPassword" placeholder="请输入新密码" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Update User Modal -->
    <a-modal
      v-model:open="showUpdateUserModal"
      title="修改用户信息"
      @ok="handleUpdateUser"
      :confirm-loading="store.loading"
    >
      <a-form layout="vertical">
        <a-form-item label="当前用户名">
          <a-input v-model:value="updateUserForm.userName" disabled />
        </a-form-item>
        <a-form-item label="新用户名">
          <a-input v-model:value="updateUserForm.newUserName" placeholder="请输入新用户名" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Generate Credit Modal -->
    <a-modal
      v-model:open="showCreditModal"
      title="生成 One-Time Credits"
      @ok="handleGenerateCredit"
      @cancel="closeCreditModal"
      :confirm-loading="store.loading"
      width="700px"
    >
      <a-form layout="vertical">
        <a-form-item label="生成数量" v-if="creditForm.generatedCredits.length === 0">
          <a-input-number
            v-model:value="creditForm.creditCount"
            :min="1"
            :max="100"
            placeholder="请输入生成数量 (1-100)"
            style="width: 100%"
          />
          <p class="help-text">
            点击下方按钮生成指定数量的 UUID Credits，用于修改 2FA 设置。
          </p>
        </a-form-item>
        <a-form-item label="生成的 Credits" v-else>
          <a-list
            :data-source="creditForm.generatedCredits"
            bordered
            style="max-height: 300px; overflow-y: auto;"
          >
            <template #renderItem="{ item, index }">
              <a-list-item>
                <a-typography-paragraph copyable>{{ item.credit_id }}</a-typography-paragraph>
              </a-list-item>
            </template>
          </a-list>
          <a-alert
            message="成功生成 Credits！"
            description="请将这些代码提供给用户用于修改 2FA 设置。"
            type="success"
            show-icon
            style="margin-top: 16px"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Change 2FA Modal -->
    <a-modal
      v-model:open="showChange2faModal"
      title="修改 2FA"
      @ok="handleChange2fa"
      :confirm-loading="store.loading"
    >
      <a-form layout="vertical">
        <a-form-item label="One-Time Credit">
          <a-input v-model:value="change2faForm.oneTimeCredit" placeholder="请输入 One-Time Credit" />
        </a-form-item>
        <a-form-item label="New 2FA Code">
          <a-input v-model:value="change2faForm.new2fa" placeholder="请输入新的 2FA 验证码" />
        </a-form-item>
      </a-form>
    </a-modal>
  </a-layout-content>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useAdminStore } from '@/stores/admin';
import { useAuthStore } from '@/stores/auth';
import { message } from 'ant-design-vue';
import {
  PlusOutlined,
  KeyOutlined,
  DeleteOutlined,
  EditOutlined,
  UploadOutlined,
} from '@ant-design/icons-vue';

const store = useAdminStore();
const authStore = useAuthStore();

// Tab management
const activeTab = ref('admins');

// Table columns
const adminColumns = [
  { title: 'ID', dataIndex: 'admin_id', key: 'admin_id' },
  { title: '用户名', dataIndex: 'admin_name', key: 'admin_name' },
  { title: '操作', key: 'actions' }
];

const teacherColumns = [
  { title: 'ID', dataIndex: 'teacher_id', key: 'teacher_id' },
  { title: '用户名', dataIndex: 'teacher_name', key: 'teacher_name' },
  { title: '操作', key: 'actions' }
];

const studentColumns = [
  { title: 'ID', dataIndex: 'student_id', key: 'student_id' },
  { title: '用户名', dataIndex: 'student_name', key: 'student_name' },
  { title: '操作', key: 'actions' }
];

// Modal states
const showAddAdminModal = ref(false);
const showAddTeacherModal = ref(false);
const showAddStudentModal = ref(false);
const showBatchAddModal = ref(false);
const showResetPasswordModal = ref(false);
const showUpdateUserModal = ref(false);
const showCreditModal = ref(false);
const showChange2faModal = ref(false);

// Form data
const newAdmin = ref({ name: '', password: '' });
const newTeacher = ref({ name: '', password: '' });
const newStudent = ref({ id: 0, name: '', password: '', type: 'undergraduate' });
const batchStudentsJson = ref('');
const selectedStudents = ref<string[]>([]);

// Reset password form
const resetPasswordForm = ref({ userName: '', newPassword: '' });

// Update user form
const updateUserForm = ref({ userName: '', newUserName: '' });

// Credit form
const creditForm = ref({
  creditCount: 1,
  generatedCredits: [] as Array<{ credit_id: string, created_at: string }>
});

// Change 2FA form
const change2faForm = ref({
  oneTimeCredit: '',
  new2fa: '',
});

onMounted(() => {
  store.fetchAllUsers();
});

// Admin operations
const handleAddAdmin = async () => {
  try {
    await store.addAdmin(newAdmin.value.name, newAdmin.value.password);
    showAddAdminModal.value = false;
    newAdmin.value = { name: '', password: '' };
    message.success('管理员添加成功！');
  } catch (err: any) {
    message.error(store.error || '添加管理员失败！');
  }
};

const handleDeleteAdmin = async (adminName: string) => {
  if (adminName === authStore.user?.user_name) {
    message.error('不能删除当前登录的管理员！');
    return;
  }
  try {
    await store.deleteAdmin(adminName);
    message.success('管理员删除成功！');
  } catch (err: any) {
    message.error(store.error || '删除管理员失败！');
  }
};

// Teacher operations
const handleAddTeacher = async () => {
  try {
    await store.addTeacher(newTeacher.value.name, newTeacher.value.password);
    showAddTeacherModal.value = false;
    newTeacher.value = { name: '', password: '' };
    message.success('教师添加成功！');
  } catch (err: any) {
    message.error(store.error || '添加教师失败！');
  }
};

const handleDeleteTeacher = async (teacherName: string) => {
  try {
    await store.deleteTeacher(teacherName);
    message.success('教师删除成功！');
  } catch (err: any) {
    message.error(store.error || '删除教师失败！');
  }
};

// Student operations
const handleAddStudent = async () => {
  try {
    await store.addStudents([{
      student_id: newStudent.value.id,
      student_name: newStudent.value.name,
      student_password: newStudent.value.password,
      student_type: newStudent.value.type
    }]);
    showAddStudentModal.value = false;
    newStudent.value = { id: 0, name: '', password: '', type: 'undergraduate' };
    message.success('学生添加成功！');
  } catch (err: any) {
    message.error(store.error || '添加学生失败！');
  }
};

const handleDeleteStudent = async (studentName: string) => {
  try {
    await store.deleteStudents([studentName]);
    message.success('学生删除成功！');
  } catch (err: any) {
    message.error(store.error || '删除学生失败！');
  }
};

const handleBatchAdd = async () => {
  try {
    const students = JSON.parse(batchStudentsJson.value);
    if (!Array.isArray(students)) {
      throw new Error('数据格式错误：应该是数组');
    }
    await store.addStudents(students);
    showBatchAddModal.value = false;
    batchStudentsJson.value = '';
    message.success(`成功批量添加 ${students.length} 个学生！`);
  } catch (err: any) {
    message.error(store.error || '批量添加学生失败！' + err.message);
  }
};

const handleBatchDelete = async () => {
  try {
    await store.deleteStudents(selectedStudents.value);
    selectedStudents.value = [];
    message.success('批量删除成功！');
  } catch (err: any) {
    message.error(store.error || '批量删除失败！');
  }
};

const onSelectChange = (selectedRowKeys: string[]) => {
  selectedStudents.value = selectedRowKeys;
};

// Reset password operations
const openResetPasswordModal = (userName: string) => {
  resetPasswordForm.value = { userName, newPassword: '' };
  showResetPasswordModal.value = true;
};

const handleResetPassword = async () => {
  if (!resetPasswordForm.value.newPassword) {
    message.error('请输入新密码');
    return;
  }
  try {
    await store.resetPassword(resetPasswordForm.value.userName, resetPasswordForm.value.newPassword);
    showResetPasswordModal.value = false;
    resetPasswordForm.value = { userName: '', newPassword: '' };
    message.success('密码重置成功！');
  } catch (err: any) {
    message.error(store.error || '密码重置失败！');
  }
};

// Update user operations
const openUpdateUserModal = (userName: string) => {
  updateUserForm.value = { userName, newUserName: userName };
  showUpdateUserModal.value = true;
};

const handleUpdateUser = async () => {
  if (!updateUserForm.value.newUserName) {
    message.error('请输入新用户名');
    return;
  }
  if (updateUserForm.value.userName === updateUserForm.value.newUserName) {
    message.error('新用户名与原用户名相同');
    return;
  }
  try {
    await store.updateUser(updateUserForm.value.userName, updateUserForm.value.newUserName);
    showUpdateUserModal.value = false;
    updateUserForm.value = { userName: '', newUserName: '' };
    message.success('用户名更新成功！');
  } catch (err: any) {
    message.error(store.error || '用户名更新失败！');
  }
};

// Generate credit operations
const openCreditModal = () => {
  creditForm.value = { creditCount: 1, generatedCredits: [] };
  showCreditModal.value = true;
};

const handleGenerateCredit = async () => {
  if (creditForm.value.creditCount < 1 || creditForm.value.creditCount > 100) {
    message.error('请输入 1-100 之间的数量');
    return;
  }
  try {
    const result = await store.generateCredit(creditForm.value.creditCount);
    creditForm.value.generatedCredits = result.credits;
    message.success(`成功生成 ${result.credits.length} 个 Credit！`);
  } catch (err: any) {
    message.error(store.error || '生成 Credit 失败！');
  }
};

const closeCreditModal = () => {
  showCreditModal.value = false;
  creditForm.value = { creditCount: 1, generatedCredits: [] };
};

// Change 2FA operations
const handleChange2fa = async () => {
  if (!change2faForm.value.oneTimeCredit || !change2faForm.value.new2fa) {
    message.error('请填写 One-Time Credit 和新的 2FA 验证码');
    return;
  }
  if (!authStore.refreshToken) {
    message.error('未找到刷新令牌，请重新登录！');
    return;
  }

  try {
    await store.change2fa(authStore.refreshToken, change2faForm.value.oneTimeCredit, change2faForm.value.new2fa);
    showChange2faModal.value = false;
    change2faForm.value = { oneTimeCredit: '', new2fa: '' };
    message.success('2FA 修改成功！');
  } catch (err: any) {
    message.error(store.error || '2FA 修改失败！');
  }
};

// Helper function to check if current user is admin
const isAdmin = () => {
  return authStore.user?.user_type === 'admin';
};

</script>

<style scoped>
.stat-card {
  text-align: center;
}

.site-page-header {
  border: 1px solid rgb(235, 237, 240);
  margin-bottom: 24px;
}

.help-text {
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
  line-height: 1.5;
  margin-top: 8px;
}
</style>

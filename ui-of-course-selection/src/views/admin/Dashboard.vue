<template>
  <div class="admin-dashboard">
    <!-- Header -->
    <div class="dashboard-header">
      <h1>管理员控制面板</h1>
      <p class="subtitle">Admin Dashboard</p>
    </div>

    <!-- Statistics Cards -->
    <div class="stats-grid">
      <div class="stat-card admin-card">
        <div class="stat-icon">👨‍💼</div>
        <div class="stat-content">
          <div class="stat-value">{{ store.admins.length }}</div>
          <div class="stat-label">管理员</div>
        </div>
      </div>
      <div class="stat-card teacher-card">
        <div class="stat-icon">👨‍🏫</div>
        <div class="stat-content">
          <div class="stat-value">{{ store.teachers.length }}</div>
          <div class="stat-label">教师</div>
        </div>
      </div>
      <div class="stat-card student-card">
        <div class="stat-icon">👨‍🎓</div>
        <div class="stat-content">
          <div class="stat-value">{{ store.students.length }}</div>
          <div class="stat-label">学生</div>
        </div>
      </div>
    </div>

    <!-- Tab Navigation -->
    <div class="tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        @click="activeTab = tab.id"
        :class="['tab-button', { active: activeTab === tab.id }]"
      >
        {{ tab.icon }} {{ tab.label }}
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="store.loading" class="loading">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>

    <!-- Error State -->
    <div v-if="store.error" class="error-message">
      <p>❌ {{ store.error }}</p>
    </div>

    <!-- Tab Content -->
    <div v-if="!store.loading" class="tab-content">
      <!-- Admin Management Tab -->
      <div v-show="activeTab === 'admins'" class="management-section">
        <div class="section-header">
          <h2>👨‍💼 管理员管理</h2>
          <button @click="showAddAdminModal = true" class="btn btn-primary">
            ➕ 添加管理员
          </button>
        </div>
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>用户名</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="admin in store.admins" :key="admin.admin_id">
                <td>{{ admin.admin_id }}</td>
                <td>{{ admin.admin_name }}</td>
                <td>
                  <div class="action-buttons">
                    <button
                      @click="openResetPasswordModal(admin.admin_name)"
                      class="btn btn-secondary btn-sm"
                    >
                      🔑 重置密码
                    </button>
                    <button
                      @click="handleDeleteAdmin(admin.admin_name)"
                      class="btn btn-danger btn-sm"
                      :disabled="admin.admin_name === authStore.user?.user_name"
                    >
                      🗑️ 删除
                    </button>
                  </div>
                </td>
              </tr>
              <tr v-if="store.admins.length === 0">
                <td colspan="3" class="empty-state">暂无管理员</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Teacher Management Tab -->
      <div v-show="activeTab === 'teachers'" class="management-section">
        <div class="section-header">
          <h2>👨‍🏫 教师管理</h2>
          <button @click="showAddTeacherModal = true" class="btn btn-primary">
            ➕ 添加教师
          </button>
        </div>
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>用户名</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="teacher in store.teachers" :key="teacher.teacher_id">
                <td>{{ teacher.teacher_id }}</td>
                <td>{{ teacher.teacher_name }}</td>
                <td>
                  <div class="action-buttons">
                    <button
                      @click="openResetPasswordModal(teacher.teacher_name)"
                      class="btn btn-secondary btn-sm"
                    >
                      🔑 重置密码
                    </button>
                    <button
                      @click="openUpdateUserModal(teacher.teacher_name)"
                      class="btn btn-info btn-sm"
                    >
                      ✏️ 修改信息
                    </button>
                    <button
                      @click="handleDeleteTeacher(teacher.teacher_name)"
                      class="btn btn-danger btn-sm"
                    >
                      🗑️ 删除
                    </button>
                  </div>
                </td>
              </tr>
              <tr v-if="store.teachers.length === 0">
                <td colspan="3" class="empty-state">暂无教师</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Student Management Tab -->
      <div v-show="activeTab === 'students'" class="management-section">
        <div class="section-header">
          <h2>👨‍🎓 学生管理</h2>
          <div class="button-group">
            <button @click="showAddStudentModal = true" class="btn btn-primary">
              ➕ 添加学生
            </button>
            <button @click="showBatchAddModal = true" class="btn btn-secondary">
              📋 批量添加
            </button>
          </div>
        </div>
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>
                  <input
                    type="checkbox"
                    @change="toggleSelectAll"
                    :checked="selectedStudents.length === store.students.length && store.students.length > 0"
                  />
                </th>
                <th>ID</th>
                <th>用户名</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="student in store.students" :key="student.student_id">
                <td>
                  <input
                    type="checkbox"
                    :value="student.student_name"
                    v-model="selectedStudents"
                  />
                </td>
                <td>{{ student.student_id }}</td>
                <td>{{ student.student_name }}</td>
                <td>
                  <div class="action-buttons">
                    <button
                      @click="openResetPasswordModal(student.student_name)"
                      class="btn btn-secondary btn-sm"
                    >
                      🔑 重置密码
                    </button>
                    <button
                      @click="openUpdateUserModal(student.student_name)"
                      class="btn btn-info btn-sm"
                    >
                      ✏️ 修改信息
                    </button>
                    <button
                      @click="handleDeleteStudent(student.student_name)"
                      class="btn btn-danger btn-sm"
                    >
                      🗑️ 删除
                    </button>
                  </div>
                </td>
              </tr>
              <tr v-if="store.students.length === 0">
                <td colspan="4" class="empty-state">暂无学生</td>
              </tr>
            </tbody>
          </table>
          <div v-if="selectedStudents.length > 0" class="batch-actions">
            <button @click="handleBatchDelete" class="btn btn-danger">
              🗑️ 批量删除 ({{ selectedStudents.length }})
            </button>
          </div>
        </div>
      </div>

      <!-- Credit Management Tab -->
      <div v-show="activeTab === 'credits'" class="management-section">
        <div class="section-header">
          <h2>🎫 Credit 管理</h2>
          <button @click="openCreditModal()" class="btn btn-primary">
            ➕ 生成 Credits
          </button>
        </div>
        <div class="credit-info-box">
          <h3>📝 关于 One-Time Credits</h3>
          <p>One-Time Credits 是用于修改 2FA 设置的一次性凭证。</p>
          <ul>
            <li>✅ 每个 Credit 使用 UUID 算法生成，全局唯一</li>
            <li>✅ 任何用户都可以使用这些 Credits</li>
            <li>✅ 每个 Credit 只能使用一次</li>
            <li>✅ 可以一次生成多个 Credits（最多 100 个）</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Add Admin Modal -->
    <div v-if="showAddAdminModal" class="modal-overlay" @click.self="showAddAdminModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>添加管理员</h3>
          <button @click="showAddAdminModal = false" class="close-btn">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>用户名</label>
            <input v-model="newAdmin.name" type="text" placeholder="请输入管理员用户名" />
          </div>
          <div class="form-group">
            <label>密码</label>
            <input v-model="newAdmin.password" type="password" placeholder="请输入密码" />
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showAddAdminModal = false" class="btn btn-secondary">取消</button>
          <button @click="handleAddAdmin" class="btn btn-primary" :disabled="!newAdmin.name || !newAdmin.password">
            确认添加
          </button>
        </div>
      </div>
    </div>

    <!-- Add Teacher Modal -->
    <div v-if="showAddTeacherModal" class="modal-overlay" @click.self="showAddTeacherModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>添加教师</h3>
          <button @click="showAddTeacherModal = false" class="close-btn">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>用户名</label>
            <input v-model="newTeacher.name" type="text" placeholder="请输入教师用户名" />
          </div>
          <div class="form-group">
            <label>密码</label>
            <input v-model="newTeacher.password" type="password" placeholder="请输入密码" />
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showAddTeacherModal = false" class="btn btn-secondary">取消</button>
          <button @click="handleAddTeacher" class="btn btn-primary" :disabled="!newTeacher.name || !newTeacher.password">
            确认添加
          </button>
        </div>
      </div>
    </div>

    <!-- Add Student Modal -->
    <div v-if="showAddStudentModal" class="modal-overlay" @click.self="showAddStudentModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>添加学生</h3>
          <button @click="showAddStudentModal = false" class="close-btn">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>学号</label>
            <input v-model.number="newStudent.id" type="number" placeholder="请输入学号" />
          </div>
          <div class="form-group">
            <label>用户名</label>
            <input v-model="newStudent.name" type="text" placeholder="请输入学生用户名" />
          </div>
          <div class="form-group">
            <label>密码</label>
            <input v-model="newStudent.password" type="password" placeholder="请输入密码" />
          </div>
          <div class="form-group">
            <label>类型</label>
            <select v-model="newStudent.type">
              <option value="undergraduate">本科生</option>
              <option value="graduate">研究生</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showAddStudentModal = false" class="btn btn-secondary">取消</button>
          <button @click="handleAddStudent" class="btn btn-primary" :disabled="!newStudent.id || !newStudent.name || !newStudent.password">
            确认添加
          </button>
        </div>
      </div>
    </div>

    <!-- Batch Add Students Modal -->
    <div v-if="showBatchAddModal" class="modal-overlay" @click.self="showBatchAddModal = false">
      <div class="modal modal-large">
        <div class="modal-header">
          <h3>批量添加学生</h3>
          <button @click="showBatchAddModal = false" class="close-btn">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>批量数据（JSON 格式）</label>
            <textarea
              v-model="batchStudentsJson"
              rows="10"
              placeholder='[{"student_id": 2001, "student_name": "student1", "student_password": "password", "student_type": "undergraduate"}]'
            ></textarea>
            <p class="help-text">
              格式示例：每个学生包含 student_id, student_name, student_password, student_type 字段
            </p>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showBatchAddModal = false" class="btn btn-secondary">取消</button>
          <button @click="handleBatchAdd" class="btn btn-primary">
            确认批量添加
          </button>
        </div>
      </div>
    </div>

    <!-- Reset Password Modal -->
    <div v-if="showResetPasswordModal" class="modal-overlay" @click.self="showResetPasswordModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>重置密码</h3>
          <button @click="showResetPasswordModal = false" class="close-btn">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>用户名</label>
            <input v-model="resetPasswordForm.userName" type="text" disabled />
          </div>
          <div class="form-group">
            <label>新密码</label>
            <input v-model="resetPasswordForm.newPassword" type="password" placeholder="请输入新密码" />
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showResetPasswordModal = false" class="btn btn-secondary">取消</button>
          <button @click="handleResetPassword" class="btn btn-primary" :disabled="!resetPasswordForm.newPassword">
            确认重置
          </button>
        </div>
      </div>
    </div>

    <!-- Update User Modal -->
    <div v-if="showUpdateUserModal" class="modal-overlay" @click.self="showUpdateUserModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>修改用户信息</h3>
          <button @click="showUpdateUserModal = false" class="close-btn">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>当前用户名</label>
            <input v-model="updateUserForm.userName" type="text" disabled />
          </div>
          <div class="form-group">
            <label>新用户名</label>
            <input v-model="updateUserForm.newUserName" type="text" placeholder="请输入新用户名" />
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showUpdateUserModal = false" class="btn btn-secondary">取消</button>
          <button @click="handleUpdateUser" class="btn btn-primary" :disabled="!updateUserForm.newUserName">
            确认修改
          </button>
        </div>
      </div>
    </div>

    <!-- Generate Credit Modal -->
    <div v-if="showCreditModal" class="modal-overlay" @click.self="closeCreditModal">
      <div class="modal modal-large">
        <div class="modal-header">
          <h3>生成 One-Time Credits</h3>
          <button @click="closeCreditModal" class="close-btn">✕</button>
        </div>
        <div class="modal-body">
          <div v-if="creditForm.generatedCredits.length === 0" class="form-group">
            <label>生成数量</label>
            <input
              v-model.number="creditForm.creditCount"
              type="number"
              min="1"
              max="100"
              placeholder="请输入生成数量 (1-100)"
            />
            <p class="help-text">
              点击下方按钮生成指定数量的 UUID Credits，用于修改 2FA 设置。
            </p>
          </div>
          <div v-else class="form-group">
            <label>生成的 Credits ({{ creditForm.generatedCredits.length }} 个)</label>
            <div class="credits-list">
              <div
                v-for="(credit, index) in creditForm.generatedCredits"
                :key="credit.credit_id"
                class="credit-item"
              >
                <span class="credit-index">{{ index + 1 }}.</span>
                <input
                  :value="credit.credit_id"
                  type="text"
                  readonly
                  class="credit-input"
                />
                <button
                  @click="copyToClipboard(credit.credit_id)"
                  class="btn btn-secondary btn-sm"
                >
                  📋 复制
                </button>
              </div>
            </div>
            <p class="help-text success-text">
              ✅ 成功生成 {{ creditForm.generatedCredits.length }} 个 Credits！请将这些代码提供给用户用于修改 2FA 设置。
            </p>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeCreditModal" class="btn btn-secondary">关闭</button>
          <button
            v-if="creditForm.generatedCredits.length === 0"
            @click="handleGenerateCredit"
            class="btn btn-primary"
          >
            🎫 生成 Credits
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useAdminStore } from '@/stores/admin';
import { useAuthStore } from '@/stores/auth';

const store = useAdminStore();
const authStore = useAuthStore();

// Tab management
const activeTab = ref('admins');
const tabs = [
  { id: 'admins', label: '管理员管理', icon: '👨‍💼' },
  { id: 'teachers', label: '教师管理', icon: '👨‍🏫' },
  { id: 'students', label: '学生管理', icon: '👨‍🎓' },
  { id: 'credits', label: 'Credit 管理', icon: '🎫' }
];

// Modal states
const showAddAdminModal = ref(false);
const showAddTeacherModal = ref(false);
const showAddStudentModal = ref(false);
const showBatchAddModal = ref(false);
const showResetPasswordModal = ref(false);
const showUpdateUserModal = ref(false);
const showCreditModal = ref(false);

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

onMounted(() => {
  store.fetchAllUsers();
});

// Admin operations
const handleAddAdmin = async () => {
  try {
    await store.addAdmin(newAdmin.value.name, newAdmin.value.password);
    showAddAdminModal.value = false;
    newAdmin.value = { name: '', password: '' };
    alert('✅ 管理员添加成功！');
  } catch (error: any) {
    alert('❌ ' + error.message);
  }
};

const handleDeleteAdmin = async (adminName: string) => {
  if (adminName === authStore.user?.user_name) {
    alert('❌ 不能删除当前登录的管理员！');
    return;
  }
  if (!confirm(`确定要删除管理员 "${adminName}" 吗？`)) return;
  try {
    await store.deleteAdmin(adminName);
    alert('✅ 管理员删除成功！');
  } catch (error: any) {
    alert('❌ ' + error.message);
  }
};

// Teacher operations
const handleAddTeacher = async () => {
  try {
    await store.addTeacher(newTeacher.value.name, newTeacher.value.password);
    showAddTeacherModal.value = false;
    newTeacher.value = { name: '', password: '' };
    alert('✅ 教师添加成功！');
  } catch (error: any) {
    alert('❌ ' + error.message);
  }
};

const handleDeleteTeacher = async (teacherName: string) => {
  if (!confirm(`确定要删除教师 "${teacherName}" 吗？`)) return;
  try {
    await store.deleteTeacher(teacherName);
    alert('✅ 教师删除成功！');
  } catch (error: any) {
    alert('❌ ' + error.message);
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
    alert('✅ 学生添加成功！');
  } catch (error: any) {
    alert('❌ ' + error.message);
  }
};

const handleDeleteStudent = async (studentName: string) => {
  if (!confirm(`确定要删除学生 "${studentName}" 吗？`)) return;
  try {
    await store.deleteStudents([studentName]);
    alert('✅ 学生删除成功！');
  } catch (error: any) {
    alert('❌ ' + error.message);
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
    alert(`✅ 成功批量添加 ${students.length} 个学生！`);
  } catch (error: any) {
    alert('❌ ' + error.message);
  }
};

const handleBatchDelete = async () => {
  if (!confirm(`确定要删除选中的 ${selectedStudents.value.length} 个学生吗？`)) return;
  try {
    await store.deleteStudents(selectedStudents.value);
    selectedStudents.value = [];
    alert('✅ 批量删除成功！');
  } catch (error: any) {
    alert('❌ ' + error.message);
  }
};

const toggleSelectAll = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.checked) {
    selectedStudents.value = store.students.map(s => s.student_name);
  } else {
    selectedStudents.value = [];
  }
};

// Reset password operations
const openResetPasswordModal = (userName: string) => {
  resetPasswordForm.value = { userName, newPassword: '' };
  showResetPasswordModal.value = true;
};

const handleResetPassword = async () => {
  if (!resetPasswordForm.value.newPassword) {
    alert('❌ 请输入新密码');
    return;
  }
  try {
    await store.resetPassword(resetPasswordForm.value.userName, resetPasswordForm.value.newPassword);
    showResetPasswordModal.value = false;
    resetPasswordForm.value = { userName: '', newPassword: '' };
    alert('✅ 密码重置成功！');
  } catch (error: any) {
    alert('❌ ' + error.message);
  }
};

// Update user operations
const openUpdateUserModal = (userName: string) => {
  updateUserForm.value = { userName, newUserName: userName };
  showUpdateUserModal.value = true;
};

const handleUpdateUser = async () => {
  if (!updateUserForm.value.newUserName) {
    alert('❌ 请输入新用户名');
    return;
  }
  if (updateUserForm.value.userName === updateUserForm.value.newUserName) {
    alert('❌ 新用户名与原用户名相同');
    return;
  }
  try {
    await store.updateUser(updateUserForm.value.userName, updateUserForm.value.newUserName);
    showUpdateUserModal.value = false;
    updateUserForm.value = { userName: '', newUserName: '' };
    alert('✅ 用户名更新成功！');
  } catch (error: any) {
    alert('❌ ' + error.message);
  }
};

// Generate credit operations
const openCreditModal = () => {
  creditForm.value = { creditCount: 1, generatedCredits: [] };
  showCreditModal.value = true;
};

const handleGenerateCredit = async () => {
  if (creditForm.value.creditCount < 1 || creditForm.value.creditCount > 100) {
    alert('❌ 请输入 1-100 之间的数量');
    return;
  }
  try {
    const result = await store.generateCredit(creditForm.value.creditCount);
    creditForm.value.generatedCredits = result.credits;
    alert(`✅ 成功生成 ${result.credits.length} 个 Credit！`);
  } catch (error: any) {
    alert('❌ ' + error.message);
  }
};

const closeCreditModal = () => {
  showCreditModal.value = false;
  creditForm.value = { creditCount: 1, generatedCredits: [] };
};

// Copy to clipboard
const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text);
    alert('✅ 已复制到剪贴板！');
  } catch (error) {
    alert('❌ 复制失败');
  }
};
</script>


<style scoped>
.admin-dashboard {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.dashboard-header {
  margin-bottom: 2rem;
}

.dashboard-header h1 {
  font-size: 32px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 8px 0;
}

.subtitle {
  color: #6b7280;
  font-size: 16px;
  margin: 0;
}

/* Tab Navigation */
.tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 2rem;
  border-bottom: 2px solid #e5e7eb;
  padding-bottom: 0;
}

.tab-button {
  padding: 0.75rem 1.5rem;
  background: transparent;
  border: none;
  border-bottom: 3px solid transparent;
  color: #6b7280;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: -2px;
}

.tab-button:hover {
  color: #667eea;
  background: #f3f4f6;
}

.tab-button.active {
  color: #667eea;
  border-bottom-color: #667eea;
  font-weight: 600;
}

.tab-content {
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Statistics Cards */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.stat-icon {
  font-size: 48px;
  line-height: 1;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 36px;
  font-weight: 700;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
}

.admin-card .stat-value {
  color: #667eea;
}

.teacher-card .stat-value {
  color: #f5576c;
}

.student-card .stat-value {
  color: #00f2fe;
}

/* Loading & Error */
.loading {
  text-align: center;
  padding: 3rem;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e5e7eb;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-message {
  background: #fee;
  border: 1px solid #fcc;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
  color: #c00;
}

/* Management Sections */
.management-sections {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.management-section {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.section-header h2 {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  color: #1f2937;
}

.button-group {
  display: flex;
  gap: 0.5rem;
}

/* Table */
.table-container {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table thead {
  background: #f9fafb;
}

.data-table th {
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  color: #374151;
  font-size: 14px;
  border-bottom: 2px solid #e5e7eb;
}

.data-table td {
  padding: 1rem;
  border-bottom: 1px solid #e5e7eb;
  color: #1f2937;
}

.data-table tbody tr:hover {
  background: #f9fafb;
}

.empty-state {
  text-align: center;
  color: #9ca3af;
  padding: 2rem !important;
}

/* Batch Actions */
.batch-actions {
  padding: 1rem 1.5rem;
  background: #f9fafb;
  border-top: 1px solid #e5e7eb;
}

/* Buttons */
.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.btn-primary {
  background: #667eea;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #5568d3;
}

.btn-secondary {
  background: #6b7280;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #4b5563;
}

.btn-danger {
  background: #ef4444;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #dc2626;
}

.btn-info {
  background: #3b82f6;
  color: white;
}

.btn-info:hover:not(:disabled) {
  background: #2563eb;
}

.btn-warning {
  background: #f59e0b;
  color: white;
}

.btn-warning:hover:not(:disabled) {
  background: #d97706;
}

.btn-sm {
  padding: 0.375rem 0.75rem;
  font-size: 13px;
}

/* Action Buttons */
.action-buttons {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 500px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: modalSlideIn 0.3s ease-out;
}

.modal-large {
  max-width: 700px;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: #9ca3af;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #f3f4f6;
  color: #1f2937;
}

.modal-body {
  padding: 1.5rem;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1.5rem;
  border-top: 1px solid #e5e7eb;
}

/* Form */
.form-group {
  margin-bottom: 1.25rem;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #374151;
  font-size: 14px;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 0.625rem 0.875rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.2s;
  font-family: inherit;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-group textarea {
  resize: vertical;
  font-family: 'Courier New', monospace;
}

.help-text {
  margin-top: 0.5rem;
  font-size: 13px;
  color: #6b7280;
}

.success-text {
  color: #10b981;
  font-weight: 500;
}

/* Credit Display */
.credit-display {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.credit-input {
  flex: 1;
  font-size: 24px;
  font-weight: 700;
  text-align: center;
  letter-spacing: 0.1em;
  color: #667eea;
  font-family: 'Courier New', monospace;
}

/* Credit Info Box */
.credit-info-box {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 2rem;
  border-radius: 12px;
  margin-top: 1.5rem;
}

.credit-info-box h3 {
  margin: 0 0 1rem 0;
  font-size: 20px;
  font-weight: 600;
}

.credit-info-box p {
  margin: 0 0 1rem 0;
  opacity: 0.95;
}

.credit-info-box ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.credit-info-box li {
  padding: 0.5rem 0;
  opacity: 0.95;
}

/* Credits List */
.credits-list {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1rem;
  background: #f8fafc;
}

.credit-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: white;
  border-radius: 6px;
  margin-bottom: 0.75rem;
  border: 1px solid #e2e8f0;
}

.credit-item:last-child {
  margin-bottom: 0;
}

.credit-index {
  font-weight: 600;
  color: #667eea;
  min-width: 30px;
}

.credit-item .credit-input {
  flex: 1;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  padding: 0.5rem;
  border: 1px solid #cbd5e0;
  border-radius: 4px;
  background: #f7fafc;
}

.modal-large {
  max-width: 700px;
  width: 90%;
}

/* Responsive */
@media (max-width: 768px) {
  .admin-dashboard {
    padding: 1rem;
  }

  .dashboard-header h1 {
    font-size: 24px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .button-group {
    width: 100%;
    flex-direction: column;
  }

  .button-group .btn {
    width: 100%;
    justify-content: center;
  }

  .data-table {
    font-size: 13px;
  }

  .data-table th,
  .data-table td {
    padding: 0.75rem 0.5rem;
  }
}
</style>

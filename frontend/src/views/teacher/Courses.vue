<template>
  <div>
    <h1>{{ t('teacher.myCourses') }}</h1>
    <a-button @click="loadCourses" :loading="loading" style="margin-bottom: 16px">
      {{ t('common.refresh') }}
    </a-button>
    <a-table :columns="columns" :data-source="courses" :loading="loading" row-key="course_id">
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'actions'">
          <a-space>
            <a-button size="small" @click="viewStudents(record)">
              {{ t('teacher.viewStudents') || '查看学生' }}
            </a-button>
            <a-button size="small" @click="editCourse(record)">{{ t('common.edit') }}</a-button>
            <a-popconfirm :title="t('teacher.deleteCourseConfirm')" @confirm="deleteCourse(record)">
              <a-button size="small" danger>{{ t('common.delete') }}</a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- Student Management Modal -->
    <a-modal
      v-model:open="studentModalVisible"
      :title="t('teacher.manageStudents') || '管理学生'"
      width="800px"
      :footer="null"
    >
      <div v-if="selectedCourse">
        <h3>{{ selectedCourse.course_name }}</h3>
        <p>{{ t('course.capacity') }}: {{ selectedCourse.course_selected || 0 }} / {{ selectedCourse.course_capacity }}</p>

        <!-- Add Students Section -->
        <a-card size="small" style="margin-bottom: 16px;">
          <template #title>{{ t('teacher.addStudents') || '添加学生' }}</template>
          <a-space direction="vertical" style="width: 100%;">
            <!-- Manual Add -->
            <a-space>
              <a-select
                v-model:value="selectedStudentIds"
                mode="multiple"
                :placeholder="t('teacher.searchStudents') || '搜索学生'"
                style="width: 400px;"
                show-search
                :filter-option="filterStudentOption"
                :loading="studentsLoading"
              >
                <a-select-option v-for="student in availableStudents" :key="student.user_id" :value="student.user_id">
                  {{ student.username }} ({{ student.name || student.user_id }})
                </a-select-option>
              </a-select>
              <a-button type="primary" @click="addStudentsToCourse" :loading="addingStudents">
                {{ t('common.add') || '添加' }}
              </a-button>
            </a-space>

            <!-- Bulk Import -->
            <a-space>
              <a-button @click="showBulkAddModal">
                {{ t('teacher.bulkAddStudents') || '批量添加学生' }}
              </a-button>
            </a-space>
          </a-space>
        </a-card>

        <!-- Enrolled Students List -->
        <a-card size="small">
          <template #title>{{ t('teacher.enrolledStudents') || '已选学生' }}</template>
          <a-table
            :columns="studentColumns"
            :data-source="enrolledStudents"
            :loading="studentsLoading"
            row-key="user_id"
            size="small"
            :pagination="{ pageSize: 10 }"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'actions'">
                <a-popconfirm
                  :title="t('teacher.removeStudentConfirm') || '确定要移除此学生吗？'"
                  @confirm="removeStudentFromCourse(record)"
                >
                  <a-button size="small" danger>
                    {{ t('common.remove') || '移除' }}
                  </a-button>
                </a-popconfirm>
              </template>
            </template>
          </a-table>
        </a-card>
      </div>
    </a-modal>

    <!-- Bulk Add Students Modal -->
    <a-modal
      v-model:open="bulkAddModalVisible"
      :title="t('teacher.bulkAddStudents') || '批量添加学生'"
      @ok="handleBulkAdd"
      :confirm-loading="bulkAddLoading"
    >
      <a-textarea
        v-model:value="bulkAddText"
        :placeholder="t('teacher.bulkAddPlaceholder') || '每行一个用户名\\n例如：\\nstudent1\\nstudent2\\nstudent3'"
        :rows="10"
      />
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/store/auth'
import teacherApi from '@/api/teacher'

const router = useRouter()
const { t } = useI18n()
const authStore = useAuthStore()
const loading = ref(false)
const courses = ref([])
const studentModalVisible = ref(false)
const selectedCourse = ref(null)
const enrolledStudents = ref([])
const availableStudents = ref([])
const studentsLoading = ref(false)
const selectedStudentIds = ref([])
const addingStudents = ref(false)
const bulkAddModalVisible = ref(false)
const bulkAddText = ref('')
const bulkAddLoading = ref(false)

// 列定义使用 computed，确保标题为字符串并随语言切换更新
const columns = computed(() => [
  { title: t('course.courseId'), dataIndex: 'course_id', key: 'course_id' },
  { title: t('course.courseName'), dataIndex: 'course_name', key: 'course_name' },
  { title: t('course.credits'), dataIndex: 'course_credit', key: 'course_credit' },
  { title: t('course.type'), dataIndex: 'course_type', key: 'course_type' },
  { title: t('course.location'), dataIndex: 'course_location', key: 'course_location' },
  { title: t('course.capacity'), dataIndex: 'course_capacity', key: 'course_capacity' },
  { title: t('course.selected') || 'Selected', dataIndex: 'course_selected', key: 'course_selected' },
  { title: t('common.actions'), key: 'actions', width: 250 },
])

const studentColumns = computed(() => [
  { title: t('user.userId'), dataIndex: 'user_id', key: 'user_id' },
  { title: t('user.username'), dataIndex: 'username', key: 'username' },
  { title: t('user.name') || '姓名', dataIndex: 'name', key: 'name' },
  { title: t('common.actions'), key: 'actions' },
])

const loadCourses = async () => {
  loading.value = true
  try {
  const response = await teacherApi.getCourses(authStore.accessToken?.value || authStore.accessToken)
    courses.value = response.courses || []
  } catch (error) {
    message.error(error.message || t('message.loadCoursesError'))
  } finally {
    loading.value = false
  }
}

const viewStudents = async (course) => {
  selectedCourse.value = course
  studentModalVisible.value = true
  await loadEnrolledStudents(course.course_id)
  await loadAvailableStudents()
}

const loadEnrolledStudents = async (courseId) => {
  studentsLoading.value = true
  try {
    const response = await teacherApi.getCourseStudents(
      authStore.accessToken?.value || authStore.accessToken,
      courseId
    )
    enrolledStudents.value = response.students || []
  } catch (error) {
    message.error(error.message || t('message.loadStudentsError') || '加载学生列表失败')
  } finally {
    studentsLoading.value = false
  }
}

const loadAvailableStudents = async () => {
  try {
    const response = await teacherApi.getStudents(
      authStore.accessToken?.value || authStore.accessToken
    )
    availableStudents.value = response.users || response.students || []
  } catch (error) {
    message.error(error.message || t('message.loadUsersError'))
  }
}

const filterStudentOption = (input, option) => {
  const label = option.label || option.value || ''
  return label.toString().toLowerCase().includes(input.toLowerCase())
}

const addStudentsToCourse = async () => {
  if (!selectedStudentIds.value || selectedStudentIds.value.length === 0) {
    message.warning(t('message.selectStudents') || '请选择学生')
    return
  }

  addingStudents.value = true
  try {
    await teacherApi.addStudentsToCourse(
      authStore.accessToken?.value || authStore.accessToken,
      selectedCourse.value.course_id,
      selectedStudentIds.value
    )
    message.success(t('message.studentsAddedSuccess') || '学生添加成功')
    selectedStudentIds.value = []
    await loadEnrolledStudents(selectedCourse.value.course_id)
    await loadCourses()
  } catch (error) {
    message.error(error.message || t('message.addStudentsError') || '添加学生失败')
  } finally {
    addingStudents.value = false
  }
}

const removeStudentFromCourse = async (student) => {
  try {
    await teacherApi.removeStudent(
      authStore.accessToken?.value || authStore.accessToken,
      selectedCourse.value.course_id,
      student.user_id
    )
    message.success(t('message.studentRemovedSuccess') || '学生移除成功')
    await loadEnrolledStudents(selectedCourse.value.course_id)
    await loadCourses()
  } catch (error) {
    message.error(error.message || t('message.removeStudentError') || '移除学生失败')
  }
}

const showBulkAddModal = () => {
  bulkAddModalVisible.value = true
  bulkAddText.value = ''
}

const handleBulkAdd = async () => {
  if (!bulkAddText.value.trim()) {
    message.warning(t('message.enterUsernames') || '请输入用户名')
    return
  }

  bulkAddLoading.value = true
  try {
    const usernames = bulkAddText.value.split('\n').map(u => u.trim()).filter(u => u)
    await teacherApi.bulkAddStudentsToCourse(
      authStore.accessToken?.value || authStore.accessToken,
      selectedCourse.value.course_id,
      usernames
    )
    message.success(t('message.bulkAddSuccess') || '批量添加成功')
    bulkAddModalVisible.value = false
    bulkAddText.value = ''
    await loadEnrolledStudents(selectedCourse.value.course_id)
    await loadCourses()
  } catch (error) {
    message.error(error.message || t('message.bulkAddError') || '批量添加失败')
  } finally {
    bulkAddLoading.value = false
  }
}

const editCourse = (course) => {
  router.push(`/teacher/edit/${course.course_id}`)
}

const deleteCourse = async (course) => {
  try {
  await teacherApi.deleteCourse(authStore.accessToken?.value || authStore.accessToken, course.course_id)
    message.success(t('message.courseDeletedSuccess'))
    loadCourses()
  } catch (error) {
    message.error(error.message || t('message.deleteCourseError'))
  }
}

onMounted(() => {
  loadCourses()
})
</script>

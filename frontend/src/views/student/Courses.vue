<template>
  <div>
    <h1>Available Courses</h1>
    
    <a-space style="margin-bottom: 16px">
      <a-select
        v-model:value="courseType"
        placeholder="Filter by type"
        style="width: 200px"
        @change="loadCourses"
      >
        <a-select-option value="">All Types</a-select-option>
        <a-select-option value="required">Required</a-select-option>
        <a-select-option value="elective">Elective</a-select-option>
      </a-select>
      
      <a-button @click="loadCourses" :loading="loading">
        Refresh
      </a-button>
    </a-space>

    <a-table
      :columns="columns"
      :data-source="courses"
      :loading="loading"
      :pagination="pagination"
      @change="handleTableChange"
      row-key="course_id"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'course_left'">
          <a-tag :color="record.course_left > 10 ? 'green' : record.course_left > 0 ? 'orange' : 'red'">
            {{ record.course_left }}
          </a-tag>
        </template>
        
        <template v-if="column.key === 'actions'">
          <a-space>
            <a-button
              type="primary"
              size="small"
              :disabled="record.course_left === 0"
              :loading="selectingCourse === record.course_id"
              @click="selectCourse(record)"
            >
              Select
            </a-button>
            <a-button size="small" @click="showCourseDetail(record)">
              Details
            </a-button>
          </a-space>
        </template>
      </template>
    </a-table>

    <a-modal
      v-model:open="detailModalVisible"
      title="Course Details"
      :footer="null"
      width="600px"
    >
      <a-descriptions v-if="selectedCourse" :column="1" bordered>
        <a-descriptions-item label="Course Name">
          {{ selectedCourse.course_name }}
        </a-descriptions-item>
        <a-descriptions-item label="Credits">
          {{ selectedCourse.course_credit }}
        </a-descriptions-item>
        <a-descriptions-item label="Type">
          {{ selectedCourse.course_type }}
        </a-descriptions-item>
        <a-descriptions-item label="Location">
          {{ selectedCourse.course_location }}
        </a-descriptions-item>
        <a-descriptions-item label="Capacity">
          {{ selectedCourse.course_selected }} / {{ selectedCourse.course_capacity }}
        </a-descriptions-item>
        <a-descriptions-item label="Available Seats">
          <a-tag :color="selectedCourse.course_left > 10 ? 'green' : selectedCourse.course_left > 0 ? 'orange' : 'red'">
            {{ selectedCourse.course_left }}
          </a-tag>
        </a-descriptions-item>
      </a-descriptions>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/store/auth'
import studentApi from '@/api/student'

const authStore = useAuthStore()

const loading = ref(false)
const courses = ref([])
const courseType = ref('')
const selectingCourse = ref(null)
const detailModalVisible = ref(false)
const selectedCourse = ref(null)

const pagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
})

const columns = [
  { title: 'Course ID', dataIndex: 'course_id', key: 'course_id' },
  { title: 'Course Name', dataIndex: 'course_name', key: 'course_name' },
  { title: 'Credits', dataIndex: 'course_credit', key: 'course_credit' },
  { title: 'Type', dataIndex: 'course_type', key: 'course_type' },
  { title: 'Location', dataIndex: 'course_location', key: 'course_location' },
  { title: 'Available', dataIndex: 'course_left', key: 'course_left' },
  { title: 'Actions', key: 'actions' },
]

const loadCourses = async () => {
  loading.value = true
  try {
    const response = await studentApi.getAvailableCourses(
      authStore.accessToken,
      courseType.value || null,
      pagination.value.current,
      pagination.value.pageSize
    )
    courses.value = response.courses
    pagination.value.total = response.total
  } catch (error) {
    message.error(error.message || 'Failed to load courses')
  } finally {
    loading.value = false
  }
}

const handleTableChange = (pag) => {
  pagination.value.current = pag.current
  pagination.value.pageSize = pag.pageSize
  loadCourses()
}

const selectCourse = async (course) => {
  selectingCourse.value = course.course_id
  try {
    const response = await studentApi.selectCourse(authStore.accessToken, course.course_id)
    message.success(response.message || 'Course selection submitted to queue')
    if (response.task_id) {
      message.info(`Queue position: ${response.position}`)
    }
    setTimeout(() => loadCourses(), 2000)
  } catch (error) {
    message.error(error.message || 'Failed to select course')
  } finally {
    selectingCourse.value = null
  }
}

const showCourseDetail = async (course) => {
  try {
    const detail = await studentApi.getCourseDetail(authStore.accessToken, course.course_id)
    selectedCourse.value = detail
    detailModalVisible.value = true
  } catch (error) {
    message.error(error.message || 'Failed to load course details')
  }
}

onMounted(() => {
  loadCourses()
})
</script>

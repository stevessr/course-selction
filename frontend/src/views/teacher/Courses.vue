<template>
  <div>
    <h1>My Courses</h1>
    <a-button @click="loadCourses" :loading="loading" style="margin-bottom: 16px">
      Refresh
    </a-button>
    <a-table :columns="columns" :data-source="courses" :loading="loading" row-key="course_id">
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'actions'">
          <a-space>
            <a-button size="small" @click="editCourse(record)">Edit</a-button>
            <a-popconfirm title="Delete this course?" @confirm="deleteCourse(record)">
              <a-button size="small" danger>Delete</a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/store/auth'
import teacherApi from '@/api/teacher'

const authStore = useAuthStore()
const loading = ref(false)
const courses = ref([])

const columns = [
  { title: 'ID', dataIndex: 'course_id', key: 'course_id' },
  { title: 'Name', dataIndex: 'course_name', key: 'course_name' },
  { title: 'Credits', dataIndex: 'course_credit', key: 'course_credit' },
  { title: 'Type', dataIndex: 'course_type', key: 'course_type' },
  { title: 'Location', dataIndex: 'course_location', key: 'course_location' },
  { title: 'Capacity', dataIndex: 'course_capacity', key: 'course_capacity' },
  { title: 'Selected', dataIndex: 'course_selected', key: 'course_selected' },
  { title: 'Actions', key: 'actions' },
]

const loadCourses = async () => {
  loading.value = true
  try {
    const response = await teacherApi.getCourses(authStore.accessToken)
    courses.value = response.courses || []
  } catch (error) {
    message.error(error.message || 'Failed to load courses')
  } finally {
    loading.value = false
  }
}

const editCourse = (course) => {
  message.info('Edit functionality to be implemented')
}

const deleteCourse = async (course) => {
  try {
    await teacherApi.deleteCourse(authStore.accessToken, course.course_id)
    message.success('Course deleted successfully')
    loadCourses()
  } catch (error) {
    message.error(error.message || 'Failed to delete course')
  }
}

onMounted(() => {
  loadCourses()
})
</script>

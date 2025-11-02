<template>
  <div>
    <h1>My Selected Courses</h1>
    
    <a-button @click="loadCourses" :loading="loading" style="margin-bottom: 16px">
      Refresh
    </a-button>

    <a-alert
      v-if="courses.length > 0"
      type="info"
      :message="`Total Credits: ${totalCredit}`"
      style="margin-bottom: 16px"
      show-icon
    />

    <a-table
      :columns="columns"
      :data-source="courses"
      :loading="loading"
      row-key="course_id"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'actions'">
          <a-popconfirm
            title="Are you sure you want to drop this course?"
            @confirm="deselectCourse(record)"
          >
            <a-button
              type="primary"
              danger
              size="small"
              :loading="droppingCourse === record.course_id"
            >
              Drop Course
            </a-button>
          </a-popconfirm>
        </template>
      </template>
    </a-table>

    <a-empty v-if="!loading && courses.length === 0" description="No courses selected yet" />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/store/auth'
import studentApi from '@/api/student'

const authStore = useAuthStore()

const loading = ref(false)
const courses = ref([])
const droppingCourse = ref(null)

const totalCredit = computed(() => {
  return courses.value.reduce((sum, course) => sum + (course.course_credit || 0), 0)
})

const columns = [
  { title: 'Course ID', dataIndex: 'course_id', key: 'course_id' },
  { title: 'Course Name', dataIndex: 'course_name', key: 'course_name' },
  { title: 'Credits', dataIndex: 'course_credit', key: 'course_credit' },
  { title: 'Type', dataIndex: 'course_type', key: 'course_type' },
  { title: 'Location', dataIndex: 'course_location', key: 'course_location' },
  { title: 'Actions', key: 'actions' },
]

const loadCourses = async () => {
  loading.value = true
  try {
  const response = await studentApi.getSelectedCourses(authStore.accessToken?.value || authStore.accessToken)
    courses.value = response.courses
  } catch (error) {
    message.error(error.message || 'Failed to load selected courses')
  } finally {
    loading.value = false
  }
}

const deselectCourse = async (course) => {
  droppingCourse.value = course.course_id
  try {
  const response = await studentApi.deselectCourse(authStore.accessToken?.value || authStore.accessToken, course.course_id)
    message.success(response.message || 'Course drop submitted to queue')
    setTimeout(() => loadCourses(), 2000)
  } catch (error) {
    message.error(error.message || 'Failed to drop course')
  } finally {
    droppingCourse.value = null
  }
}

onMounted(() => {
  loadCourses()
})
</script>

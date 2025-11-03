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
            <a-button size="small" @click="editCourse(record)">{{ t('common.edit') }}</a-button>
            <a-popconfirm :title="t('teacher.deleteCourseConfirm')" @confirm="deleteCourse(record)">
              <a-button size="small" danger>{{ t('common.delete') }}</a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>
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

// 列定义使用 computed，确保标题为字符串并随语言切换更新
const columns = computed(() => [
  { title: t('course.courseId'), dataIndex: 'course_id', key: 'course_id' },
  { title: t('course.courseName'), dataIndex: 'course_name', key: 'course_name' },
  { title: t('course.credits'), dataIndex: 'course_credit', key: 'course_credit' },
  { title: t('course.type'), dataIndex: 'course_type', key: 'course_type' },
  { title: t('course.location'), dataIndex: 'course_location', key: 'course_location' },
  { title: t('course.capacity'), dataIndex: 'course_capacity', key: 'course_capacity' },
  { title: t('course.selected') || 'Selected', dataIndex: 'course_selected', key: 'course_selected' },
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

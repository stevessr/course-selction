<template>
  <div>
    <h1>{{ t('student.selectedCourses') }}</h1>
    
    <a-button @click="loadCourses" :loading="loading" style="margin-bottom: 16px">
      {{ t('common.refresh') }}
    </a-button>

    <a-alert
      v-if="courses.length > 0"
      type="info"
      :message="`${t('student.totalCredits')}: ${totalCredit}`"
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
            :title="t('student.dropCourseConfirm')"
            @confirm="deselectCourse(record)"
          >
            <a-button
              type="primary"
              danger
              size="small"
              :loading="droppingCourse === record.course_id"
            >
              {{ t('student.dropCourse') }}
            </a-button>
          </a-popconfirm>
        </template>
      </template>
    </a-table>

    <a-empty v-if="!loading && courses.length === 0" :description="t('student.noCourses')" />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/store/auth'
import studentApi from '@/api/student'

const { t } = useI18n()

const authStore = useAuthStore()

const loading = ref(false)
const courses = ref([])
const droppingCourse = ref(null)

const totalCredit = computed(() => {
  return courses.value.reduce((sum, course) => sum + (course.course_credit || 0), 0)
})

// 使用 computed 生成整列定义，确保 title 为字符串而不是 ref，避免渲染为 [object Object]
const columns = computed(() => [
  { title: t('course.courseId'), dataIndex: 'course_id', key: 'course_id' },
  { title: t('course.courseName'), dataIndex: 'course_name', key: 'course_name' },
  { title: t('course.credits'), dataIndex: 'course_credit', key: 'course_credit' },
  { title: t('course.type'), dataIndex: 'course_type', key: 'course_type' },
  { title: t('course.location'), dataIndex: 'course_location', key: 'course_location' },
  { title: t('common.actions'), key: 'actions' },
])

const loadCourses = async () => {
  loading.value = true
  try {
  const response = await studentApi.getSelectedCourses(authStore.accessToken?.value || authStore.accessToken)
    courses.value = response.courses
  } catch (error) {
    message.error(error.message || t('student.loadSelectedCoursesFailed'))
  } finally {
    loading.value = false
  }
}

const deselectCourse = async (course) => {
  droppingCourse.value = course.course_id
  try {
  const response = await studentApi.deselectCourse(authStore.accessToken?.value || authStore.accessToken, course.course_id)
    message.success(response.message || t('student.courseDropSubmitted'))
    setTimeout(() => loadCourses(), 2000)
  } catch (error) {
    message.error(error.message || t('student.courseDropFailed'))
  } finally {
    droppingCourse.value = null
  }
}

onMounted(() => {
  loadCourses()
})
</script>

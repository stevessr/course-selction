<template>
  <div>
    <h1>{{ t('student.availableCourses') }}</h1>
    
    <a-card style="margin-bottom: 16px">
      <h3>{{ t('student.searchAndFilters') }}</h3>
      <a-row :gutter="[16, 16]">
        <a-col :span="6">
          <a-input-search
            v-model:value="searchText"
            :placeholder="t('course.searchCourseName')"
            @search="handleSearch"
            allow-clear
          />
        </a-col>
        <a-col :span="6">
          <a-select
            v-model:value="courseType"
            :placeholder="t('course.courseType')"
            style="width: 100%"
            @change="handleSearch"
            allow-clear
          >
            <a-select-option value="">{{ t('course.allTypes') }}</a-select-option>
            <a-select-option value="required">{{ t('course.required') }}</a-select-option>
            <a-select-option value="elective">{{ t('course.elective') }}</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-select
            v-model:value="filterTag"
            :placeholder="t('course.filterByTag')"
            style="width: 100%"
            @change="handleSearch"
            allow-clear
          >
            <a-select-option v-for="tag in availableTags" :key="tag" :value="tag">
              {{ tag }}
            </a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-select
            v-model:value="filterWeekday"
            :placeholder="t('course.filterByWeekday')"
            style="width: 100%"
            @change="handleSearch"
            allow-clear
          >
            <a-select-option value="monday">{{ t('course.monday') }}</a-select-option>
            <a-select-option value="tuesday">{{ t('course.tuesday') }}</a-select-option>
            <a-select-option value="wednesday">{{ t('course.wednesday') }}</a-select-option>
            <a-select-option value="thursday">{{ t('course.thursday') }}</a-select-option>
            <a-select-option value="friday">{{ t('course.friday') }}</a-select-option>
            <a-select-option value="saturday">{{ t('course.saturday') }}</a-select-option>
            <a-select-option value="sunday">{{ t('course.sunday') }}</a-select-option>
          </a-select>
        </a-col>
      </a-row>
      <a-row :gutter="[16, 16]" style="margin-top: 16px">
        <a-col :span="12">
          <a-space>
            <span>{{ t('course.timeRange') }}:</span>
            <a-time-picker
              v-model:value="filterTimeStart"
              format="HH:mm"
              :placeholder="t('course.startTime')"
              @change="handleSearch"
            />
            <span>-</span>
            <a-time-picker
              v-model:value="filterTimeEnd"
              format="HH:mm"
              :placeholder="t('course.endTime')"
              @change="handleSearch"
            />
          </a-space>
        </a-col>
        <a-col :span="12">
          <a-button @click="clearFilters" style="float: right">
            {{ t('common.clearFilters') }}
          </a-button>
          <a-button @click="loadCourses" :loading="loading" type="primary" style="float: right; margin-right: 8px">
            {{ t('common.refresh') }}
          </a-button>
        </a-col>
      </a-row>
    </a-card>

    <a-table
      :columns="columns"
      :data-source="courses"
      :loading="loading"
      :pagination="pagination"
      @change="handleTableChange"
      row-key="course_id"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'course_time'">
          <div>{{ formatTime(record.course_time_begin) }} - {{ formatTime(record.course_time_end) }}</div>
        </template>

        <template v-if="column.key === 'course_left'">
          <a-tag :color="record.course_left > 10 ? 'green' : record.course_left > 0 ? 'orange' : 'red'">
            {{ record.course_left }}
          </a-tag>
        </template>
        
        <template v-if="column.key === 'actions'">
          <a-space direction="vertical" size="small" style="width: 100%">
            <a-button
              type="primary"
              size="small"
              :disabled="isDisabled(record)"
              :loading="selectingCourse === record.course_id"
              @click="selectCourse(record)"
              style="width: 100%"
            >
              {{ hasTimeConflict(record) ? t('course.timeConflict') : t('common.select') }}
            </a-button>
            <a-button size="small" @click="showCourseDetail(record)" style="width: 100%">
              {{ t('common.details') }}
            </a-button>
          </a-space>
        </template>
      </template>
    </a-table>

    <a-modal
      v-model:open="detailModalVisible"
      :title="t('course.courseDetails')"
      :footer="null"
      width="600px"
    >
      <a-descriptions v-if="selectedCourse" :column="1" bordered>
        <a-descriptions-item :label="t('course.courseName')">
          {{ selectedCourse.course_name }}
        </a-descriptions-item>
        <a-descriptions-item :label="t('course.credits')">
          {{ selectedCourse.course_credit }}
        </a-descriptions-item>
        <a-descriptions-item :label="t('course.type')">
          {{ selectedCourse.course_type }}
        </a-descriptions-item>
        <a-descriptions-item :label="t('course.location')">
          {{ selectedCourse.course_location }}
        </a-descriptions-item>
        <a-descriptions-item :label="t('course.time')">
          {{ formatTime(selectedCourse.course_time_begin) }} - {{ formatTime(selectedCourse.course_time_end) }}
        </a-descriptions-item>
        <a-descriptions-item :label="t('course.capacity')">
          {{ selectedCourse.course_selected }} / {{ selectedCourse.course_capacity }}
        </a-descriptions-item>
        <a-descriptions-item :label="t('course.availableSeats')">
          <a-tag :color="selectedCourse.course_left > 10 ? 'green' : selectedCourse.course_left > 0 ? 'orange' : 'red'">
            {{ selectedCourse.course_left }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item :label="t('course.tags')" v-if="selectedCourse.course_tags && selectedCourse.course_tags.length > 0">
          <a-tag v-for="tag in selectedCourse.course_tags" :key="tag" color="blue">{{ tag }}</a-tag>
        </a-descriptions-item>
        <a-descriptions-item :label="t('course.notes')" v-if="selectedCourse.course_notes">
          {{ selectedCourse.course_notes }}
        </a-descriptions-item>
      </a-descriptions>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/store/auth'
import studentApi from '@/api/student'
import dayjs from 'dayjs'

const { t } = useI18n()
const authStore = useAuthStore()

const loading = ref(false)
const courses = ref([])
const selectedCourses = ref([])
const courseType = ref('')
const selectingCourse = ref(null)
const detailModalVisible = ref(false)
const selectedCourse = ref(null)

// Filter state
const searchText = ref('')
const filterTag = ref('')
const filterWeekday = ref('')
const filterTimeStart = ref(null)
const filterTimeEnd = ref(null)
const availableTags = ref([])

const pagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
})

const columns = computed(() => [
  { title: t('course.courseId'), dataIndex: 'course_id', key: 'course_id' },
  { title: t('course.courseName'), dataIndex: 'course_name', key: 'course_name' },
  { title: t('course.credits'), dataIndex: 'course_credit', key: 'course_credit' },
  { title: t('course.type'), dataIndex: 'course_type', key: 'course_type' },
  { title: t('course.location'), dataIndex: 'course_location', key: 'course_location' },
  { title: t('course.time'), key: 'course_time' },
  { title: t('course.available'), dataIndex: 'course_left', key: 'course_left' },
  { title: t('common.actions'), key: 'actions' },
])

const loadSelectedCourses = async () => {
  try {
    const response = await studentApi.getSelectedCourses(
      authStore.accessToken?.value || authStore.accessToken
    )
    selectedCourses.value = response.courses || []
  } catch (error) {
    console.error('Failed to load selected courses:', error)
  }
}

const hasTimeConflict = (course) => {
  // Check if the course conflicts with any selected courses
  for (const selected of selectedCourses.value) {
    // Simple time overlap check: courses conflict if their time ranges overlap
    const courseStart = course.course_time_begin
    const courseEnd = course.course_time_end
    const selectedStart = selected.course_time_begin
    const selectedEnd = selected.course_time_end
    
    // Check if times overlap
    if (courseStart < selectedEnd && courseEnd > selectedStart) {
      return true
    }
  }
  return false
}

const isDisabled = (course) => {
  return course.course_left === 0 || hasTimeConflict(course)
}

const clearFilters = () => {
  searchText.value = ''
  courseType.value = ''
  filterTag.value = ''
  filterWeekday.value = ''
  filterTimeStart.value = null
  filterTimeEnd.value = null
  handleSearch()
}

const handleSearch = () => {
  pagination.value.current = 1
  loadCourses()
}

const filterCourses = (coursesList) => {
  let filtered = coursesList

  // Search by name
  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    filtered = filtered.filter(c => c.course_name.toLowerCase().includes(search))
  }

  // Filter by tag
  if (filterTag.value) {
    filtered = filtered.filter(c => 
      c.course_tags && c.course_tags.includes(filterTag.value)
    )
  }

  // Filter by weekday
  if (filterWeekday.value) {
    filtered = filtered.filter(c => 
      c.course_schedule && c.course_schedule[filterWeekday.value]
    )
  }

  // Filter by time range
  if (filterTimeStart.value && filterTimeEnd.value) {
    const startTime = filterTimeStart.value.hour() * 100 + filterTimeStart.value.minute()
    const endTime = filterTimeEnd.value.hour() * 100 + filterTimeEnd.value.minute()
    
    filtered = filtered.filter(c => {
      // Course time must be within the filter range
      return c.course_time_begin >= startTime && c.course_time_end <= endTime
    })
  }

  return filtered
}

const loadCourses = async () => {
  loading.value = true
  try {
    // Load all courses without pagination first
    const response = await studentApi.getAvailableCourses(
      authStore.accessToken?.value || authStore.accessToken,
      courseType.value || null,
      1,
      1000 // Get all courses for filtering
    )
    
    // Apply frontend filters
    const allCourses = response.courses || []
    const filtered = filterCourses(allCourses)
    
    // Extract unique tags from all courses
    const tagsSet = new Set()
    allCourses.forEach(course => {
      if (course.course_tags) {
        course.course_tags.forEach(tag => tagsSet.add(tag))
      }
    })
    availableTags.value = Array.from(tagsSet)
    
    // Apply pagination to filtered results
    const start = (pagination.value.current - 1) * pagination.value.pageSize
    const end = start + pagination.value.pageSize
    courses.value = filtered.slice(start, end)
    pagination.value.total = filtered.length
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
  const response = await studentApi.selectCourse(authStore.accessToken?.value || authStore.accessToken, course.course_id)
    message.success(response.message || 'Course selection submitted to queue')
    if (response.task_id) {
      const position = response.position || 'Unknown'
      message.info(`Queue position: ${position}`)
    }
    setTimeout(async () => {
      await loadSelectedCourses()
      await loadCourses()
    }, 2000)
  } catch (error) {
    message.error(error.message || 'Failed to select course')
  } finally {
    selectingCourse.value = null
  }
}

const showCourseDetail = async (course) => {
  try {
  const detail = await studentApi.getCourseDetail(authStore.accessToken?.value || authStore.accessToken, course.course_id)
    selectedCourse.value = detail
    detailModalVisible.value = true
  } catch (error) {
    message.error(error.message || 'Failed to load course details')
  }
}

// Format time from integer to HH:MM format (e.g., 800 -> "08:00", 1350 -> "13:50")
const formatTime = (time) => {
  if (!time) return 'N/A'
  const hour = Math.floor(time / 100)
  const minute = time % 100
  return `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`
}

onMounted(async () => {
  await loadSelectedCourses()
  await loadCourses()
})
</script>

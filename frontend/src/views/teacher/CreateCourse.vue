<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
      <h1>{{ t('teacher.createNewCourse') }}</h1>
      <a-button @click="showImportModal">
        <template #icon><UploadOutlined /></template>
        {{ t('import.bulkImportCourses') }}
      </a-button>
    </div>
    <a-form :model="form" @finish="handleSubmit" layout="vertical" style="max-width: 600px">
      <a-form-item :label="t('course.courseName')" name="course_name" :rules="[{ required: true }]">
        <a-input v-model:value="form.course_name" />
      </a-form-item>
      <a-form-item :label="t('course.credits')" name="course_credit" :rules="[{ required: true }]">
        <a-input-number v-model:value="form.course_credit" :min="0" :step="0.5" style="width: 100%" />
        <div style="margin-top: 4px; color: #666; font-size: 12px;">
          {{ t('course.credits') }} {{ '0.5, 1.5, 2.5' }}
        </div>
      </a-form-item>
      <a-form-item :label="t('course.type')" name="course_type" :rules="[{ required: true }]">
        <a-select v-model:value="form.course_type">
          <a-select-option value="required">{{ t('course.required') }}</a-select-option>
          <a-select-option value="elective">{{ t('course.elective') }}</a-select-option>
        </a-select>
      </a-form-item>
      <a-form-item :label="t('course.location')" name="course_location" :rules="[{ required: true }]">
        <a-input v-model:value="form.course_location" />
      </a-form-item>
      <a-form-item :label="t('course.capacity')" name="course_capacity" :rules="[{ required: true }]">
        <a-input-number v-model:value="form.course_capacity" :min="1" style="width: 100%" />
      </a-form-item>
      <a-form-item :label="t('course.startTime')" name="course_time_begin" :rules="[{ required: true, message: t('course.startTime') }]">
        <a-time-picker
          v-model:value="form.course_time_begin"
          format="HH:mm"
          :minuteStep="5"
          style="width: 100%"
          :placeholder="t('course.startTime')"
        />
      </a-form-item>
      <a-form-item :label="t('course.endTime')" name="course_time_end" :rules="[{ required: true, message: t('course.endTime') }]">
        <a-time-picker
          v-model:value="form.course_time_end"
          format="HH:mm"
          :minuteStep="5"
          style="width: 100%"
          :placeholder="t('course.endTime')"
        />
      </a-form-item>
      <a-form-item :label="t('course.courseSchedule')" name="course_schedule">
        <div style="margin-bottom: 8px; color: #666; font-size: 12px;">
          {{ t('course.courseSchedule') }}
        </div>
        <a-checkbox-group v-model:value="selectedDays" style="width: 100%">
          <a-row>
            <a-col :span="8" v-for="day in weekDays" :key="day.value">
              <a-checkbox :value="day.value">{{ day.label }}</a-checkbox>
            </a-col>
          </a-row>
        </a-checkbox-group>
      </a-form-item>
      <a-form-item :label="t('course.courseTags')" name="course_tags">
        <a-select 
          v-model:value="form.course_tags" 
          mode="tags" 
          :placeholder="t('tag.enterTags')"
          style="width: 100%"
        >
        </a-select>
        <div style="margin-top: 8px; color: #666; font-size: 12px;">
          {{ t('tag.formatDescription', ['username,tag1,tag2']) }}
        </div>
      </a-form-item>
      <a-form-item :label="t('course.notes')" name="course_notes">
        <a-textarea v-model:value="form.course_notes" :rows="3" :placeholder="t('course.courseNotes') || ''" />
      </a-form-item>
      <a-form-item :label="t('course.cost')" name="course_cost">
        <a-input-number v-model:value="form.course_cost" :min="0" style="width: 100%" :placeholder="'0'" />
      </a-form-item>
      <a-form-item>
        <a-space>
          <a-button type="primary" html-type="submit" :loading="loading">{{ t('common.create') }}</a-button>
          <a-button @click="$router.push('/teacher/courses')">{{ t('common.cancel') }}</a-button>
        </a-space>
      </a-form-item>
    </a-form>

    <!-- Import Modal -->
    <a-modal
      v-model:open="importModalVisible"
      :title="t('import.bulkImportCourses')"
      @ok="handleImportCourses"
      @cancel="resetImportForm"
      :confirm-loading="importLoading"
      width="700px"
    >
      <a-form layout="vertical">
        <a-form-item :label="t('import.csvFormatHint', { fields: t('import.coursesFormat') })">
          <a-textarea
            v-model:value="importText"
            :placeholder="t('import.coursesExample')"
            :rows="12"
          />
        </a-form-item>
        <a-alert
          :message="t('import.format')"
          :description="t('import.timeFormatNote') + ' ' + (t('import.formatNote') || '')"
          type="info"
          show-icon
          style="margin-top: 8px;"
        />
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { UploadOutlined } from '@ant-design/icons-vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/store/auth'
import teacherApi from '@/api/teacher'
import dayjs from 'dayjs'

const router = useRouter()
const { t } = useI18n()
const authStore = useAuthStore()
const loading = ref(false)

// Note: keep time values inside the form model so a-form can validate them

const weekDays = [
  { label: t('course.monday'), value: 'monday' },
  { label: t('course.tuesday'), value: 'tuesday' },
  { label: t('course.wednesday'), value: 'wednesday' },
  { label: t('course.thursday'), value: 'thursday' },
  { label: t('course.friday'), value: 'friday' },
  { label: t('course.saturday'), value: 'saturday' },
  { label: t('course.sunday'), value: 'sunday' },
]

const selectedDays = ref([])

// Import modal state
const importModalVisible = ref(false)
const importLoading = ref(false)
const importText = ref('')

const form = ref({
  course_name: '',
  course_credit: 3,
  course_type: 'required',
  course_location: '',
  course_capacity: 30,
  course_teacher_id: authStore.user?.user_id || 0,
  course_schedule: {},
  course_tags: [],
  course_notes: '',
  course_cost: 0,
  // time fields stored as dayjs objects for the time pickers
  course_time_begin: dayjs('08:00', 'HH:mm'),
  course_time_end: dayjs('09:50', 'HH:mm'),
})

// Update course_schedule based on selected days
watch(selectedDays, (newDays) => {
  const schedule = {}
  newDays.forEach(day => {
    schedule[day] = [1] // Default to period 1, can be extended later
  })
  form.value.course_schedule = schedule
}, { deep: true })

// Convert time from dayjs to integer format (e.g., "08:00" -> 800)
const timeToInt = (time) => {
  if (!time) return 0
  const hour = time.hour()
  const minute = time.minute()
  return hour * 100 + minute
}

const handleSubmit = async () => {
  // Validate time range
  if (form.value.course_time_begin && form.value.course_time_end) {
    if (
      form.value.course_time_end.isBefore(form.value.course_time_begin) ||
      form.value.course_time_end.isSame(form.value.course_time_begin)
    ) {
      message.error(t('message.endTimeAfterStart'))
      return
    }
  }

  loading.value = true
  try {
    // Convert time picker values to integer format
    const courseData = {
      ...form.value,
      course_time_begin: timeToInt(form.value.course_time_begin),
      course_time_end: timeToInt(form.value.course_time_end),
    }

    await teacherApi.createCourse(authStore.accessToken?.value || authStore.accessToken, courseData)
    message.success(t('message.courseCreatedSuccess'))
    router.push('/teacher/courses')
  } catch (error) {
    message.error(error.message || t('message.createCourseError'))
  } finally {
    loading.value = false
  }
}

const showImportModal = () => {
  importModalVisible.value = true
}

const resetImportForm = () => {
  importText.value = ''
  importModalVisible.value = false
}

const handleImportCourses = async () => {
  if (!importText.value || !importText.value.trim()) {
    message.warning(t('message.enterCsvData'))
    return
  }

  importLoading.value = true
  try {
    // Parse CSV and create course objects
    const lines = importText.value.trim().split('\n')
    const coursesData = []

    for (const line of lines) {
      if (!line.trim()) continue

      const parts = line.split(',').map(p => p.trim())
      if (parts.length < 7) {
        message.error(`Invalid line format: ${line}`)
        continue
      }

      const tags = parts.length > 7 && parts[7] ? parts[7].split(';').map(t => t.trim()).filter(t => t) : []

      coursesData.push({
        course_name: parts[0],
        course_credit: parseFloat(parts[1]) || 3,
        course_type: parts[2] || 'elective',
        course_location: parts[3] || 'TBD',
        course_capacity: parseInt(parts[4]) || 30,
        course_time_begin: parseInt(parts[5]) || 800,
        course_time_end: parseInt(parts[6]) || 950,
        course_tags: tags,
        course_schedule: {},
        course_notes: '',
        course_cost: 0,
      })
    }

    if (coursesData.length === 0) {
      message.error(t('message.noValidCourses'))
      return
    }

    const result = await teacherApi.bulkImportCourses(authStore.accessToken?.value || authStore.accessToken, coursesData)

    if (result.error_count > 0) {
      message.warning(t('message.importComplete', { success: result.imported_count, failed: result.error_count }))
      console.log('Import errors:', result.errors)
    } else {
      message.success(t('import.importSuccess', { count: result.imported_count }))
    }

    resetImportForm()
    router.push('/teacher/courses')
  } catch (error) {
    message.error(t('message.importError') + ': ' + (error.response?.data?.detail || error.message))
  } finally {
    importLoading.value = false
  }
}
</script>

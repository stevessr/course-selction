<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
      <h1>Create New Course</h1>
      <a-button @click="showImportModal">
        <template #icon><UploadOutlined /></template>
        批量导入 / Bulk Import
      </a-button>
    </div>
    <a-form :model="form" @finish="handleSubmit" layout="vertical" style="max-width: 600px">
      <a-form-item label="Course Name" name="course_name" :rules="[{ required: true }]">
        <a-input v-model:value="form.course_name" />
      </a-form-item>
      <a-form-item label="Credits" name="course_credit" :rules="[{ required: true }]">
        <a-input-number v-model:value="form.course_credit" :min="0" :step="0.5" style="width: 100%" />
        <div style="margin-top: 4px; color: #666; font-size: 12px;">
          Credits can be decimal values (e.g., 0.5, 1.5, 2.5)
        </div>
      </a-form-item>
      <a-form-item label="Type" name="course_type" :rules="[{ required: true }]">
        <a-select v-model:value="form.course_type">
          <a-select-option value="required">Required</a-select-option>
          <a-select-option value="elective">Elective</a-select-option>
        </a-select>
      </a-form-item>
      <a-form-item label="Location" name="course_location" :rules="[{ required: true }]">
        <a-input v-model:value="form.course_location" />
      </a-form-item>
      <a-form-item label="Capacity" name="course_capacity" :rules="[{ required: true }]">
        <a-input-number v-model:value="form.course_capacity" :min="1" style="width: 100%" />
      </a-form-item>
      <a-form-item label="Time Begin" name="course_time_begin" :rules="[{ required: true, message: 'Please select start time' }]">
        <a-time-picker
          v-model:value="form.course_time_begin"
          format="HH:mm"
          :minuteStep="5"
          style="width: 100%"
          placeholder="Select start time"
        />
      </a-form-item>
      <a-form-item label="Time End" name="course_time_end" :rules="[{ required: true, message: 'Please select end time' }]">
        <a-time-picker
          v-model:value="form.course_time_end"
          format="HH:mm"
          :minuteStep="5"
          style="width: 100%"
          placeholder="Select end time"
        />
      </a-form-item>
      <a-form-item label="Course Schedule" name="course_schedule">
        <div style="margin-bottom: 8px; color: #666; font-size: 12px;">
          Select the days when this course is scheduled
        </div>
        <a-checkbox-group v-model:value="selectedDays" style="width: 100%">
          <a-row>
            <a-col :span="8" v-for="day in weekDays" :key="day.value">
              <a-checkbox :value="day.value">{{ day.label }}</a-checkbox>
            </a-col>
          </a-row>
        </a-checkbox-group>
      </a-form-item>
      <a-form-item label="Course Tags" name="course_tags">
        <a-select 
          v-model:value="form.course_tags" 
          mode="tags" 
          placeholder="Enter tags (students must have matching tags to enroll)"
          style="width: 100%"
        >
        </a-select>
        <div style="margin-top: 8px; color: #666; font-size: 12px;">
          Add tags to restrict enrollment to students with matching tags. Leave empty for no restrictions.
        </div>
      </a-form-item>
      <a-form-item label="Notes" name="course_notes">
        <a-textarea v-model:value="form.course_notes" :rows="3" placeholder="Additional course information (optional)" />
      </a-form-item>
      <a-form-item label="Cost" name="course_cost">
        <a-input-number v-model:value="form.course_cost" :min="0" style="width: 100%" placeholder="0 for free courses" />
      </a-form-item>
      <a-form-item>
        <a-space>
          <a-button type="primary" html-type="submit" :loading="loading">Create</a-button>
          <a-button @click="$router.push('/teacher/courses')">Cancel</a-button>
        </a-space>
      </a-form-item>
    </a-form>

    <!-- Import Modal -->
    <a-modal
      v-model:open="importModalVisible"
      title="批量导入课程 / Bulk Import Courses"
      @ok="handleImportCourses"
      @cancel="resetImportForm"
      :confirm-loading="importLoading"
      width="700px"
    >
      <a-form layout="vertical">
        <a-form-item label="CSV 数据 / CSV Data">
          <a-textarea
            v-model:value="importText"
            placeholder="格式 / Format: course_name,course_credit,course_type,course_location,course_capacity,course_time_begin,course_time_end,tag1;tag2;tag3&#10;例如 / Example:&#10;数学,3,required,A101,30,800,950,math;science&#10;英语,3,elective,B202,25,1000,1150,english;language"
            :rows="12"
          />
        </a-form-item>
        <a-alert
          message="格式说明 / Format"
          description="每行一门课程，格式为：课程名,学分,类型(required/elective),地点,容量,开始时间,结束时间,标签1;标签2;标签3。时间格式为24小时制数字，例如800表示8:00，1350表示13:50。Each line: course_name,credits,type,location,capacity,time_begin,time_end,tag1;tag2;tag3"
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
import { useAuthStore } from '@/store/auth'
import teacherApi from '@/api/teacher'
import dayjs from 'dayjs'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)

// Note: keep time values inside the form model so a-form can validate them

const weekDays = [
  { label: 'Monday', value: 'monday' },
  { label: 'Tuesday', value: 'tuesday' },
  { label: 'Wednesday', value: 'wednesday' },
  { label: 'Thursday', value: 'thursday' },
  { label: 'Friday', value: 'friday' },
  { label: 'Saturday', value: 'saturday' },
  { label: 'Sunday', value: 'sunday' },
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
      message.error('End time must be after start time')
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
    message.success('Course created successfully')
    router.push('/teacher/courses')
  } catch (error) {
    message.error(error.message || 'Failed to create course')
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
    message.warning('请输入CSV数据')
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
      message.error('No valid courses found in CSV')
      return
    }

    const result = await teacherApi.bulkImportCourses(authStore.accessToken?.value || authStore.accessToken, coursesData)

    if (result.error_count > 0) {
      message.warning(`导入完成: ${result.imported_count} 成功, ${result.error_count} 失败`)
      console.log('Import errors:', result.errors)
    } else {
      message.success(`成功导入 ${result.imported_count} 门课程`)
    }

    resetImportForm()
    router.push('/teacher/courses')
  } catch (error) {
    message.error('导入失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    importLoading.value = false
  }
}
</script>

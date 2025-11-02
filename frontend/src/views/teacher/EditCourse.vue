<template>
  <div>
    <h1>Edit Course</h1>
    <a-spin :spinning="loadingCourse">
      <a-form :model="form" @finish="handleSubmit" layout="vertical" style="max-width: 600px">
        <a-form-item label="Course Name" name="course_name" :rules="[{ required: true }]">
          <a-input v-model:value="form.course_name" />
        </a-form-item>
        <a-form-item label="Credits" name="course_credit" :rules="[{ required: true }]">
          <a-input-number v-model:value="form.course_credit" :min="0" style="width: 100%" />
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
        <a-form-item label="Time Begin" name="course_time_begin" :rules="[{ required: true }]">
          <a-input-number v-model:value="form.course_time_begin" style="width: 100%" />
        </a-form-item>
        <a-form-item label="Time End" name="course_time_end" :rules="[{ required: true }]">
          <a-input-number v-model:value="form.course_time_end" style="width: 100%" />
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
            <a-button type="primary" html-type="submit" :loading="loading">Update</a-button>
            <a-button @click="$router.push('/teacher/courses')">Cancel</a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-spin>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/store/auth'
import teacherApi from '@/api/teacher'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const loading = ref(false)
const loadingCourse = ref(false)

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

const form = ref({
  course_name: '',
  course_credit: 3,
  course_type: 'required',
  course_location: '',
  course_capacity: 30,
  course_time_begin: 800,
  course_time_end: 950,
  course_schedule: {},
  course_tags: [],
  course_notes: '',
  course_cost: 0,
})

// Update course_schedule based on selected days
watch(selectedDays, (newDays) => {
  const schedule = {}
  newDays.forEach(day => {
    schedule[day] = [1] // Default to period 1, can be extended later
  })
  form.value.course_schedule = schedule
}, { deep: true })

// Load course data
const loadCourse = async () => {
  const courseId = parseInt(route.params.id)
  if (!courseId) {
    message.error('Course ID is required')
    router.push('/teacher/courses')
    return
  }

  loadingCourse.value = true
  try {
    const response = await teacherApi.getCourseDetail(
      authStore.accessToken?.value || authStore.accessToken,
      courseId
    )
    
    // Populate form with course data
    form.value = {
      course_name: response.course_name || '',
      course_credit: response.course_credit || 3,
      course_type: response.course_type || 'required',
      course_location: response.course_location || '',
      course_capacity: response.course_capacity || 30,
      course_time_begin: response.course_time_begin || 800,
      course_time_end: response.course_time_end || 950,
      course_schedule: response.course_schedule || {},
      course_tags: response.course_tags || [],
      course_notes: response.course_notes || '',
      course_cost: response.course_cost || 0,
    }

    // Set selected days from course_schedule
    if (response.course_schedule && typeof response.course_schedule === 'object') {
      selectedDays.value = Object.keys(response.course_schedule)
    }
  } catch (error) {
    message.error(error.message || 'Failed to load course')
    router.push('/teacher/courses')
  } finally {
    loadingCourse.value = false
  }
}

const handleSubmit = async () => {
  const courseId = parseInt(route.params.id)
  loading.value = true
  try {
    await teacherApi.updateCourse(
      authStore.accessToken?.value || authStore.accessToken,
      courseId,
      form.value
    )
    message.success('Course updated successfully')
    router.push('/teacher/courses')
  } catch (error) {
    message.error(error.message || 'Failed to update course')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadCourse()
})
</script>

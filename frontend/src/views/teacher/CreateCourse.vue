<template>
  <div>
    <h1>Create New Course</h1>
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
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/store/auth'
import teacherApi from '@/api/teacher'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)

const form = ref({
  course_name: '',
  course_credit: 3,
  course_type: 'required',
  course_location: '',
  course_capacity: 30,
  course_time_begin: 800,
  course_time_end: 950,
  course_teacher_id: authStore.user?.user_id || 0,
  course_tags: [],
  course_notes: '',
  course_cost: 0,
})

const handleSubmit = async () => {
  loading.value = true
  try {
  await teacherApi.createCourse(authStore.accessToken?.value || authStore.accessToken, form.value)
    message.success('Course created successfully')
    router.push('/teacher/courses')
  } catch (error) {
    message.error(error.message || 'Failed to create course')
  } finally {
    loading.value = false
  }
}
</script>

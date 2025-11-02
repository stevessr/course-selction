<template>
  <div>
    <h1>My Schedule</h1>
    
    <a-button @click="loadSchedule" :loading="loading" style="margin-bottom: 16px">
      Refresh
    </a-button>

    <a-card v-if="!loading && schedule" style="margin-top: 16px">
      <a-row :gutter="[16, 16]">
        <a-col
          v-for="day in [1, 2, 3, 4, 5, 6, 7]"
          :key="day"
          :span="24"
          :md="12"
          :lg="8"
        >
          <a-card :title="getDayName(day)" size="small">
            <div v-if="schedule[day] && schedule[day].length > 0">
              <a-list
                size="small"
                :data-source="schedule[day]"
              >
                <template #renderItem="{ item }">
                  <a-list-item>
                    <a-list-item-meta>
                      <template #title>{{ item.course_name }}</template>
                      <template #description>
                        <div>{{ item.course_location }}</div>
                        <div>Time: {{ item.course_time_begin }} - {{ item.course_time_end }}</div>
                      </template>
                    </a-list-item-meta>
                  </a-list-item>
                </template>
              </a-list>
            </div>
            <a-empty v-else description="No classes" :image="null" />
          </a-card>
        </a-col>
      </a-row>
    </a-card>

    <a-empty v-if="!loading && !schedule" description="No schedule data available" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/store/auth'
import studentApi from '@/api/student'

const authStore = useAuthStore()

const loading = ref(false)
const schedule = ref(null)

const dayNames = ['', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

const getDayName = (day) => dayNames[day]

const loadSchedule = async () => {
  loading.value = true
  try {
  const response = await studentApi.getSchedule(authStore.accessToken?.value || authStore.accessToken)
    schedule.value = response.schedule
  } catch (error) {
    message.error(error.message || 'Failed to load schedule')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadSchedule()
})
</script>

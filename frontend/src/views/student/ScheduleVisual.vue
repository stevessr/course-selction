<template>
  <div class="schedule-visual">
    <a-card title="My Course Schedule" class="schedule-card">
      <!-- Week Selector -->
      <div class="week-selector">
        <a-space>
          <span>Week:</span>
          <a-select v-model:value="currentWeek" style="width: 120px" @change="loadSchedule">
            <a-select-option v-for="week in 32" :key="week" :value="week">
              Week {{ week }}
            </a-select-option>
          </a-select>
          <a-button @click="currentWeek = 1; loadSchedule()">Reset</a-button>
        </a-space>
      </div>

      <!-- Schedule Grid -->
      <div class="schedule-grid" v-if="!loading">
        <table class="timetable">
          <thead>
            <tr>
              <th class="period-header">Period</th>
              <th v-for="day in dayLabels" :key="day" class="day-header">
                {{ day }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(period, periodIndex) in allPeriods" :key="period" 
                :class="{'period-row': true, [getTimeOfDay(period)]: true}">
              <td class="period-cell">
                <div class="period-number">{{ period }}</div>
                <div class="period-time">{{ getPeriodTime(period) }}</div>
              </td>
              <td v-for="(day, dayIndex) in 7" :key="dayIndex" class="course-cell">
                <div v-if="scheduleGrid[periodIndex][dayIndex]" 
                     class="course-block"
                     :style="{ backgroundColor: scheduleGrid[periodIndex][dayIndex].color }"
                     @click="showCourseDetails(scheduleGrid[periodIndex][dayIndex])">
                  <div class="course-name">{{ scheduleGrid[periodIndex][dayIndex].course_name }}</div>
                  <div class="course-location">{{ scheduleGrid[periodIndex][dayIndex].course_location }}</div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Loading State -->
      <div v-else class="loading-state">
        <a-spin size="large" />
        <p>Loading schedule...</p>
      </div>

      <!-- Empty State -->
      <a-empty v-if="!loading && courses.length === 0" 
               description="No courses selected yet" />
    </a-card>

    <!-- Course Details Modal -->
    <a-modal v-model:visible="detailsVisible" title="Course Details" width="600px">
      <div v-if="selectedCourse" class="course-details">
        <a-descriptions bordered :column="1">
          <a-descriptions-item label="Course Name">
            {{ selectedCourse.course_name }}
          </a-descriptions-item>
          <a-descriptions-item label="Teacher">
            {{ selectedCourse.teacher_name }}
          </a-descriptions-item>
          <a-descriptions-item label="Location">
            {{ selectedCourse.course_location }}
          </a-descriptions-item>
          <a-descriptions-item label="Time">
            Period {{ selectedCourse.period_start }}-{{ selectedCourse.period_end }}
            ({{ getPeriodTime(selectedCourse.period_start) }} - 
             {{ getPeriodTime(selectedCourse.period_end).split('-')[1] }})
          </a-descriptions-item>
        </a-descriptions>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import studentApi from '@/api/student'
import { 
  getPeriodTime, 
  getPeriodLabel, 
  getTimeOfDay,
  isCourseActiveInWeek,
  formatScheduleGrid,
  getAllPeriods,
  getDayLabels
} from '@/utils/scheduleHelpers'

const loading = ref(false)
const courses = ref([])
const currentWeek = ref(1)
const scheduleGrid = ref([])
const detailsVisible = ref(false)
const selectedCourse = ref(null)

const allPeriods = getAllPeriods()
const dayLabels = getDayLabels()

const loadSchedule = async () => {
  loading.value = true
  try {
    // Get selected courses
    const response = await studentApi.getSelectedCourses()
    courses.value = response.data || []
    
    // Format into grid
    scheduleGrid.value = formatScheduleGrid(courses.value, currentWeek.value)
  } catch (error) {
    message.error('Failed to load schedule: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const showCourseDetails = (course) => {
  selectedCourse.value = course
  detailsVisible.value = true
}

onMounted(() => {
  loadSchedule()
})
</script>

<style scoped>
.schedule-visual {
  padding: 24px;
}

.schedule-card {
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.week-selector {
  margin-bottom: 24px;
  padding: 16px;
  background: #f5f5f5;
  border-radius: 4px;
}

.schedule-grid {
  overflow-x: auto;
}

.timetable {
  width: 100%;
  border-collapse: collapse;
  min-width: 800px;
}

.timetable th,
.timetable td {
  border: 1px solid #e8e8e8;
  padding: 8px;
  text-align: center;
}

.period-header,
.day-header {
  background: #fafafa;
  font-weight: 600;
  padding: 12px 8px;
}

.period-cell {
  background: #fafafa;
  min-width: 100px;
}

.period-number {
  font-size: 18px;
  font-weight: 600;
  color: #1890ff;
}

.period-time {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

.course-cell {
  min-width: 120px;
  height: 80px;
  padding: 4px;
  position: relative;
}

.course-block {
  height: 100%;
  border-radius: 4px;
  padding: 8px;
  color: white;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.course-block:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

.course-name {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 4px;
  text-align: center;
}

.course-location {
  font-size: 12px;
  opacity: 0.9;
  text-align: center;
}

.period-row.morning {
  background: #fff9e6;
}

.period-row.afternoon {
  background: #e6f7ff;
}

.period-row.evening {
  background: #f9f0ff;
}

.loading-state {
  text-align: center;
  padding: 60px 0;
}

.loading-state p {
  margin-top: 16px;
  color: #666;
}

.course-details {
  padding: 16px 0;
}
</style>

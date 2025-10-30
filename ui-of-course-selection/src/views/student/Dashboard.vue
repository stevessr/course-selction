<template>
  <a-tabs v-model:activeKey="activeTab" style="margin-top: 16px">
    <a-tab-pane key="available" tab="Available Courses">
      <AvailableCourses />
    </a-tab-pane>
    <a-tab-pane key="selected" tab="Selected Courses">
      <SelectedCourses />
    </a-tab-pane>
    <a-tab-pane key="schedule" tab="My Schedule">
      <a-card title="My Schedule">
        <a-alert v-if="store.error" :message="store.error" type="error" show-icon style="margin-bottom: 16px" />
        <a-spin v-if="store.loading" tip="Loading schedule..."></a-spin>
        <div v-else>
          <a-empty v-if="Object.keys(store.schedule).length === 0" description="No courses in your schedule." />
          <div v-else>
            <a-collapse v-model:activeKey="activeDays">
              <a-collapse-panel v-for="(courses, day) in store.schedule" :key="day" :header="`Day ${day}`">
                <a-list :data-source="courses">
                  <template #renderItem="{ item }">
                    <a-list-item>
                      <a-list-item-meta
                        :title="item.course_name"
                        :description="`Teacher: ${item.teacher_name} | Location: ${item.course_location}`"
                      />
                      <div>
                        Time: {{ item.course_time_begin }} - {{ item.course_time_end }}
                      </div>
                    </a-list-item>
                  </template>
                </a-list>
              </a-collapse-panel>
            </a-collapse>
          </div>
        </div>
      </a-card>
    </a-tab-pane>
    <a-tab-pane key="stats" tab="My Stats">
      <a-card title="My Stats">
        <a-alert v-if="store.error" :message="store.error" type="error" show-icon style="margin-bottom: 16px" />
        <a-spin v-if="store.loading" tip="Loading stats..."></a-spin>
        <div v-else-if="store.stats">
          <a-descriptions bordered :column="1">
            <a-descriptions-item label="Total Courses">{{ store.stats.total_courses }}</a-descriptions-item>
            <a-descriptions-item label="Total Credit">{{ store.stats.total_credit }}</a-descriptions-item>
            <a-descriptions-item label="Courses by Type">
              <p v-for="(count, type) in store.stats.courses_by_type" :key="type">
                {{ type }}: {{ count }}
              </p>
            </a-descriptions-item>
            <a-descriptions-item label="Credit by Type">
              <p v-for="(credit, type) in store.stats.credit_by_type" :key="type">
                {{ type }}: {{ credit }}
              </p>
            </a-descriptions-item>
          </a-descriptions>
        </div>
        <a-empty v-else description="No stats available." />
      </a-card>
    </a-tab-pane>
  </a-tabs>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import AvailableCourses from '@/components/student/AvailableCourses.vue';
import SelectedCourses from '@/components/student/SelectedCourses.vue';
import { useStudentStore } from '@/stores/student';

const store = useStudentStore();
const activeTab = ref('available');
const activeDays = ref<string[]>([]); // For collapse component

onMounted(() => {
  store.fetchAvailableCourses();
  store.fetchSelectedCourses();
  store.fetchSchedule();
  store.fetchStats();
});

watch(activeTab, (newTab) => {
  if (newTab === 'schedule') {
    store.fetchSchedule();
  } else if (newTab === 'stats') {
    store.fetchStats();
  }
});
</script>

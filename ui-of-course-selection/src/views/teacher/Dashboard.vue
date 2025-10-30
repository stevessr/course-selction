<template>
  <a-tabs v-model:activeKey="activeTab" style="margin-top: 16px">
    <a-tab-pane key="courses" tab="My Courses">
      <MyCourses />
    </a-tab-pane>
    <a-tab-pane key="stats" tab="My Stats">
      <a-card title="My Stats">
        <a-alert v-if="store.error" :message="store.error" type="error" show-icon style="margin-bottom: 16px" />
        <a-spin v-if="store.loading" tip="Loading stats..."></a-spin>
        <div v-else-if="store.stats">
          <a-descriptions bordered :column="1">
            <a-descriptions-item label="Total Courses">{{ store.stats.total_courses }}</a-descriptions-item>
            <a-descriptions-item label="Total Students">{{ store.stats.total_students }}</a-descriptions-item>
            <a-descriptions-item label="Courses by Type">
              <p v-for="(count, type) in store.stats.courses_by_type" :key="type">
                {{ type }}: {{ count }}
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
import MyCourses from '@/components/teacher/MyCourses.vue';
import { useTeacherStore } from '@/stores/teacher';

const store = useTeacherStore();
const activeTab = ref('courses');

onMounted(() => {
  store.fetchCourses();
  store.fetchStats();
});

watch(activeTab, (newTab) => {
  if (newTab === 'stats') {
    store.fetchStats();
  }
});
</script>

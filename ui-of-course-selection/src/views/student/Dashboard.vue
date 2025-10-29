<template>
  <main class="dashboard-layout">
    <div class="courses-column">
      <AvailableCourses />
    </div>
    <div class="courses-column">
      <SelectedCourses />
    </div>
  </main>
</template>

<script setup lang="ts">
import AvailableCourses from '@/components/student/AvailableCourses.vue';
import SelectedCourses from '@/components/student/SelectedCourses.vue';
</script>

<style scoped>
.dashboard-layout {
  display: flex;
  gap: 2rem;
  padding: 1rem;
}

.courses-column {
  flex: 1;
}
</style>

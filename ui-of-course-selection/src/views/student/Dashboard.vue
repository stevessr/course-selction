<template>
  <div>
    <header>
      <h1>Student Dashboard</h1>
      <button @click="handleLogout">Logout</button>
    </header>
    <main class="dashboard-layout">
      <div class="courses-column">
        <AvailableCourses />
      </div>
      <div class="courses-column">
        <SelectedCourses />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import AvailableCourses from '@/components/student/AvailableCourses.vue';
import SelectedCourses from '@/components/student/SelectedCourses.vue';

const router = useRouter();
const authStore = useAuthStore();

const handleLogout = () => {
  authStore.clearAuth();
  router.push({ name: 'Login' });
};
</script>

<style scoped>
header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #ccc;
}

.dashboard-layout {
  display: flex;
  gap: 2rem;
  padding: 1rem;
}

.courses-column {
  flex: 1;
}
</style>

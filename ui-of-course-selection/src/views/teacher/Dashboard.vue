<template>
  <div>
    <header>
      <h1>Teacher Dashboard</h1>
      <button @click="handleLogout">Logout</button>
    </header>
    <main>
      <MyCourses />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import MyCourses from '@/components/teacher/MyCourses.vue';

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
</style>

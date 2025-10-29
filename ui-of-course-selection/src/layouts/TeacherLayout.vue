<template>
  <div class="layout">
    <aside class="sidebar">
      <h2>Teacher Menu</h2>
      <nav>
        <router-link :to="{ name: 'TeacherDashboard' }">Dashboard</router-link>
        <!-- Add more teacher links here -->
      </nav>
      <button @click="handleLogout">Logout</button>
    </aside>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const router = useRouter();
const authStore = useAuthStore();

const handleLogout = () => {
  authStore.clearAuth();
  router.push({ name: 'Login' });
};
</script>

<style scoped>
.layout {
  display: flex;
  height: 100vh;
}
.sidebar {
  width: 200px;
  background-color: #f4f4f4;
  padding: 1rem;
}
.main-content {
  flex-grow: 1;
  padding: 1rem;
}
nav {
  display: flex;
  flex-direction: column;
}
</style>

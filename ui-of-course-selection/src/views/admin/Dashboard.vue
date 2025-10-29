<template>
  <div>
    <header>
      <h1>Admin Dashboard</h1>
      <button @click="handleLogout">Logout</button>
    </header>
    <main class="dashboard-layout">
      <div class="user-list">
        <h2>Admins</h2>
        <ul>
          <li v-for="user in store.admins" :key="user.admin_id">{{ user.admin_name }}</li>
        </ul>
      </div>
      <div class="user-list">
        <h2>Teachers</h2>
        <ul>
          <li v-for="user in store.teachers" :key="user.teacher_id">{{ user.teacher_name }}</li>
        </ul>
      </div>
      <div class="user-list">
        <h2>Students</h2>
        <ul>
          <li v-for="user in store.students" :key="user.student_id">{{ user.student_name }}</li>
        </ul>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useAdminStore } from '@/stores/admin';

const router = useRouter();
const authStore = useAuthStore();
const store = useAdminStore();

onMounted(() => {
  store.fetchAllUsers();
});

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

.user-list {
  flex: 1;
}
</style>

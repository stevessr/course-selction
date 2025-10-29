<template>
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
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useAdminStore } from '@/stores/admin';

const store = useAdminStore();

onMounted(() => {
  store.fetchAllUsers();
});
</script>

<style scoped>
.dashboard-layout {
  display: flex;
  gap: 2rem;
  padding: 1rem;
}

.user-list {
  flex: 1;
}
</style>

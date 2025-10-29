import { defineStore } from 'pinia';
import { ref } from 'vue';
import { loginApi } from '@/services/api';
import { useAuthStore } from './auth';

export const useAdminStore = defineStore('admin', () => {
  const admins = ref([]);
  const teachers = ref([]);
  const students = ref([]);

  const authStore = useAuthStore();

  const fetchAllUsers = async () => {
    if (!authStore.token) return;
    try {
      const [adminsRes, teachersRes, studentsRes] = await Promise.all([
        loginApi.get('/get/admin/all', { headers: { Authorization: `Bearer ${authStore.token}` } }),
        loginApi.get('/get/teacher/all', { headers: { Authorization: `Bearer ${authStore.token}` } }),
        loginApi.get('/get/students/all', { headers: { Authorization: `Bearer ${authStore.token}` } })
      ]);
      admins.value = adminsRes.data;
      teachers.value = teachersRes.data;
      students.value = studentsRes.data;
    } catch (error) {
      console.error('Failed to fetch users:', error);
    }
  };

  return {
    admins,
    teachers,
    students,
    fetchAllUsers
  };
});

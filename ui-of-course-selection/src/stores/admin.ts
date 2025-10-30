import { defineStore } from 'pinia';
import { ref } from 'vue';
import { loginApi } from '@/services/api';
import { useAuthStore } from './auth';

interface Admin {
  admin_id: number;
  admin_name: string;
}

interface Teacher {
  teacher_id: number;
  teacher_name: string;
}

interface Student {
  student_id: number;
  student_name: string;
}

export const useAdminStore = defineStore('admin', () => {
  const admins = ref<Admin[]>([]);
  const teachers = ref<Teacher[]>([]);
  const students = ref<Student[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const authStore = useAuthStore();

  const fetchAllUsers = async () => {
    if (!authStore.token) return;
    loading.value = true;
    error.value = null;
    try {
      const [adminsRes, teachersRes, studentsRes] = await Promise.all([
        loginApi.post('/get/admin/all', {}, { headers: { access_token: authStore.token } }),
        loginApi.post('/get/teacher/all', {}, { headers: { access_token: authStore.token } }),
        loginApi.post('/get/students/all', {}, { headers: { access_token: authStore.token } })
      ]);
      admins.value = adminsRes.data.admins || [];
      teachers.value = teachersRes.data.teachers || [];
      students.value = studentsRes.data.students || [];
    } catch (err: any) {
      console.error('Failed to fetch users:', err);
      error.value = err.response?.data?.detail || 'Failed to fetch users';
    } finally {
      loading.value = false;
    }
  };

  const addAdmin = async (admin_name: string, admin_password: string) => {
    if (!authStore.token) throw new Error('Not authenticated');
    try {
      await loginApi.post('/add/admin',
        { admin_name, admin_password },
        { headers: { access_token: authStore.token } }
      );
      await fetchAllUsers();
      return { success: true };
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Failed to add admin');
    }
  };

  const deleteAdmin = async (admin_name: string) => {
    if (!authStore.token) throw new Error('Not authenticated');
    try {
      await loginApi.post('/delete/admin',
        { admin_name },
        { headers: { access_token: authStore.token } }
      );
      await fetchAllUsers();
      return { success: true };
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Failed to delete admin');
    }
  };

  const addTeacher = async (teacher_name: string, teacher_password: string) => {
    if (!authStore.token) throw new Error('Not authenticated');
    try {
      await loginApi.post('/add/teacher',
        { teacher_name, teacher_password },
        { headers: { access_token: authStore.token } }
      );
      await fetchAllUsers();
      return { success: true };
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Failed to add teacher');
    }
  };

  const deleteTeacher = async (teacher_name: string) => {
    if (!authStore.token) throw new Error('Not authenticated');
    try {
      await loginApi.post('/delete/teacher',
        { teacher_name },
        { headers: { access_token: authStore.token } }
      );
      await fetchAllUsers();
      return { success: true };
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Failed to delete teacher');
    }
  };

  const addStudents = async (students: Array<{ student_id: number; student_name: string; student_password: string; student_type: string }>) => {
    if (!authStore.token) throw new Error('Not authenticated');
    try {
      await loginApi.post('/add/students',
        { students },
        { headers: { access_token: authStore.token } }
      );
      await fetchAllUsers();
      return { success: true };
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Failed to add students');
    }
  };

  const deleteStudents = async (student_names: string[]) => {
    if (!authStore.token) throw new Error('Not authenticated');
    try {
      await loginApi.post('/delete/students',
        { students: student_names },
        { headers: { access_token: authStore.token } }
      );
      await fetchAllUsers();
      return { success: true };
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Failed to delete students');
    }
  };

  const resetPassword = async (user_name: string, new_password: string) => {
    if (!authStore.token) throw new Error('Not authenticated');
    try {
      await loginApi.post('/admin/reset-password',
        { user_name, new_password },
        { headers: { access_token: authStore.token } }
      );
      return { success: true };
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Failed to reset password');
    }
  };

  const updateUser = async (user_name: string, new_user_name: string) => {
    if (!authStore.token) throw new Error('Not authenticated');
    try {
      await loginApi.post('/admin/update-user',
        { user_name, new_user_name },
        { headers: { access_token: authStore.token } }
      );
      await fetchAllUsers();
      return { success: true };
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Failed to update user');
    }
  };

  const generateCredit = async (credit_count: number = 1) => {
    if (!authStore.token) throw new Error('Not authenticated');
    try {
      const response = await loginApi.post('/admin/generate-credit',
        { credit_count },
        { headers: { access_token: authStore.token } }
      );
      return { success: true, credits: response.data.credits };
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Failed to generate credit');
    }
  };

  return {
    admins,
    teachers,
    students,
    loading,
    error,
    fetchAllUsers,
    addAdmin,
    deleteAdmin,
    addTeacher,
    deleteTeacher,
    addStudents,
    deleteStudents,
    resetPassword,
    updateUser,
    generateCredit
  };
});

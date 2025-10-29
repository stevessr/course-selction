import { defineStore } from 'pinia';
import { ref } from 'vue';
import { teacherApi } from '@/services/api';
import { useAuthStore } from './auth';

export const useTeacherStore = defineStore('teacher', () => {
  const courses = ref([]);
  const courseDetail = ref<any>(null);

  const authStore = useAuthStore();

  const fetchCourses = async () => {
    if (!authStore.token) return;
    try {
      const response = await teacherApi.get('/teacher/courses', {
        headers: { Authorization: `Bearer ${authStore.token}` }
      });
      courses.value = response.data.courses;
    } catch (error) {
      console.error('Failed to fetch teacher courses:', error);
    }
  };

  const fetchCourseDetail = async (courseId: number) => {
    if (!authStore.token) return;
    try {
      const response = await teacherApi.post('/teacher/course/detail', 
        { course_id: courseId }, 
        { headers: { Authorization: `Bearer ${authStore.token}` } 
      });
      courseDetail.value = response.data;
    } catch (error) {
      console.error('Failed to fetch teacher course detail:', error);
    }
  };

  return {
    courses,
    courseDetail,
    fetchCourses,
    fetchCourseDetail
  };
});

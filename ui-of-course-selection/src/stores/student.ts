import { defineStore } from 'pinia';
import { ref } from 'vue';
import { studentApi } from '@/services/api';
import { useAuthStore } from './auth';

export const useStudentStore = defineStore('student', () => {
  const availableCourses = ref([]);
  const selectedCourses = ref([]);
  const courseDetail = ref<any>(null);
  const queueStatus = ref<any>({});

  const authStore = useAuthStore();

  const fetchAvailableCourses = async () => {
    if (!authStore.token) return;
    try {
      const response = await studentApi.get('/student/courses/available', {
        headers: { Authorization: `Bearer ${authStore.token}` }
      });
      availableCourses.value = response.data.courses;
    } catch (error) {
      console.error('Failed to fetch available courses:', error);
    }
  };

  const fetchSelectedCourses = async () => {
    if (!authStore.token) return;
    try {
      const response = await studentApi.get('/student/courses/selected', {
        headers: { Authorization: `Bearer ${authStore.token}` }
      });
      selectedCourses.value = response.data.courses;
    } catch (error) {
      console.error('Failed to fetch selected courses:', error);
    }
  };

  const fetchCourseDetail = async (courseId: number) => {
    if (!authStore.token) return;
    try {
      const response = await studentApi.post('/student/course/detail', 
        { course_id: courseId }, 
        { headers: { Authorization: `Bearer ${authStore.token}` } 
      });
      courseDetail.value = response.data;
    } catch (error) {
      console.error('Failed to fetch course detail:', error);
    }
  };

  const selectCourse = async (courseId: number) => {
    if (!authStore.token) return;
    try {
      const response = await studentApi.post('/student/course/select', 
        { course_id: courseId }, 
        { headers: { Authorization: `Bearer ${authStore.token}` } 
      });
      // Maybe show a notification to the user
      console.log('Course selection queued:', response.data);
      fetchAvailableCourses(); // Refresh available courses
      fetchSelectedCourses(); // Refresh selected courses
    } catch (error) {
      console.error('Failed to select course:', error);
    }
  };

  const deselectCourse = async (courseId: number) => {
    if (!authStore.token) return;
    try {
      const response = await studentApi.post('/student/course/deselect', 
        { course_id: courseId }, 
        { headers: { Authorization: `Bearer ${authStore.token}` } 
      });
      console.log('Course deselection queued:', response.data);
      fetchAvailableCourses(); // Refresh available courses
      fetchSelectedCourses(); // Refresh selected courses
    } catch (error) {
      console.error('Failed to deselect course:', error);
    }
  };

  return {
    availableCourses,
    selectedCourses,
    courseDetail,
    queueStatus,
    fetchAvailableCourses,
    fetchSelectedCourses,
    fetchCourseDetail,
    selectCourse,
    deselectCourse
  };
});

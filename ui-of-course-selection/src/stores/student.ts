import { defineStore } from 'pinia';
import { ref } from 'vue';
import { studentApi } from '@/services/api';
import { useAuthStore } from './auth';

interface Course {
  course_id: number;
  course_name: string;
  course_credit: number;
  course_type: string;
  teacher_name: string;
  course_time_begin: number;
  course_time_end: number;
  course_location: string;
  course_capacity: number;
  course_selected: number;
  course_left: number;
}

interface StudentCourseDetail extends Course {
  is_selected: boolean;
}

interface ScheduleEntry {
  course_id: number;
  course_name: string;
  teacher_name: string;
  course_time_begin: number;
  course_time_end: number;
  course_location: string;
}

interface StudentStats {
  total_courses: number;
  total_credit: number;
  courses_by_type: { [key: string]: number };
  credit_by_type: { [key: string]: number };
}

interface QueueStatus {
  status: string;
  message: string;
  created_at: number;
  completed_at?: number;
}

interface Conflict {
  type: string;
  message: string;
  course_id?: number;
  course_name?: string;
}

export const useStudentStore = defineStore('student', () => {
  const availableCourses = ref<Course[]>([]);
  const selectedCourses = ref<Course[]>([]);
  const courseDetail = ref<StudentCourseDetail | null>(null);
  const schedule = ref<{ [key: number]: ScheduleEntry[] }>({});
  const stats = ref<StudentStats | null>(null);
  const queueStatus = ref<QueueStatus | null>(null);

  const loading = ref(false);
  const error = ref<string | null>(null);

  const authStore = useAuthStore();

  const fetchAvailableCourses = async () => {
    if (!authStore.token) return;
    loading.value = true;
    error.value = null;
    try {
      const response = await studentApi.get('/student/courses/available', {
        headers: { Authorization: `Bearer ${authStore.token}` }
      });
      availableCourses.value = response.data.courses;
    } catch (err: any) {
      error.value = `Failed to fetch available courses: ${err.response?.data?.detail || err.message}`;
      console.error(error.value);
    } finally {
      loading.value = false;
    }
  };

  const fetchSelectedCourses = async () => {
    if (!authStore.token) return;
    loading.value = true;
    error.value = null;
    try {
      const response = await studentApi.get('/student/courses/selected', {
        headers: { Authorization: `Bearer ${authStore.token}` }
      });
      selectedCourses.value = response.data.courses;
    } catch (err: any) {
      error.value = `Failed to fetch selected courses: ${err.response?.data?.detail || err.message}`;
      console.error(error.value);
    } finally {
      loading.value = false;
    }
  };

  const fetchCourseDetail = async (courseId: number) => {
    if (!authStore.token) return;
    loading.value = true;
    error.value = null;
    try {
      const response = await studentApi.post('/student/course/detail', 
        { course_id: courseId }, 
        { headers: { Authorization: `Bearer ${authStore.token}` } 
      });
      courseDetail.value = response.data;
    } catch (err: any) {
      error.value = `Failed to fetch course detail: ${err.response?.data?.detail || err.message}`;
      console.error(error.value);
    } finally {
      loading.value = false;
    }
  };

  const selectCourse = async (courseId: number) => {
    if (!authStore.token) return;
    loading.value = true;
    error.value = null;
    try {
      const response = await studentApi.post('/student/course/select', 
        { course_id: courseId }, 
        { headers: { Authorization: `Bearer ${authStore.token}` } 
      });
      // Handle queue_id and estimated_time if needed in UI
      console.log('Course selection queued:', response.data);
      await fetchAvailableCourses(); // Refresh available courses
      await fetchSelectedCourses(); // Refresh selected courses
      return response.data; // Return queue info
    } catch (err: any) {
      error.value = `Failed to select course: ${err.response?.data?.detail || err.message}`;
      console.error(error.value);
      throw err; // Re-throw to allow component to handle
    } finally {
      loading.value = false;
    }
  };

  const deselectCourse = async (courseId: number) => {
    if (!authStore.token) return;
    loading.value = true;
    error.value = null;
    try {
      const response = await studentApi.post('/student/course/deselect', 
        { course_id: courseId }, 
        { headers: { Authorization: `Bearer ${authStore.token}` } 
      });
      console.log('Course deselection queued:', response.data);
      await fetchAvailableCourses(); // Refresh available courses
      await fetchSelectedCourses(); // Refresh selected courses
      return response.data; // Return queue info
    } catch (err: any) {
      error.value = `Failed to deselect course: ${err.response?.data?.detail || err.message}`;
      console.error(error.value);
      throw err; // Re-throw to allow component to handle
    } finally {
      loading.value = false;
    }
  };

  const fetchSchedule = async (week?: number) => {
    if (!authStore.token) return;
    loading.value = true;
    error.value = null;
    try {
      const response = await studentApi.post('/student/schedule', 
        { week }, 
        { headers: { Authorization: `Bearer ${authStore.token}` } 
      });
      schedule.value = response.data.schedule;
    } catch (err: any) {
      error.value = `Failed to fetch schedule: ${err.response?.data?.detail || err.message}`;
      console.error(error.value);
    } finally {
      loading.value = false;
    }
  };

  const fetchStats = async () => {
    if (!authStore.token) return;
    loading.value = true;
    error.value = null;
    try {
      const response = await studentApi.post('/student/stats', 
        {}, 
        { headers: { Authorization: `Bearer ${authStore.token}` } 
      });
      stats.value = response.data;
    } catch (err: any) {
      error.value = `Failed to fetch student stats: ${err.response?.data?.detail || err.message}`;
      console.error(error.value);
    } finally {
      loading.value = false;
    }
  };

  const fetchQueueStatus = async (queueId: string) => {
    if (!authStore.token) return;
    loading.value = true;
    error.value = null;
    try {
      const response = await studentApi.post('/student/queue/status', 
        { queue_id: queueId }, 
        { headers: { Authorization: `Bearer ${authStore.token}` } 
      });
      queueStatus.value = response.data;
      return response.data;
    } catch (err: any) {
      error.value = `Failed to fetch queue status: ${err.response?.data?.detail || err.message}`;
      console.error(error.value);
      throw err;
    } finally {
      loading.value = false;
    }
  };

  const checkCourseConflict = async (courseId: number): Promise<{ can_select: boolean; conflicts: Conflict[] }> => {
    if (!authStore.token) return { can_select: false, conflicts: [] };
    loading.value = true;
    error.value = null;
    try {
      const response = await studentApi.post('/student/course/check', 
        { course_id: courseId }, 
        { headers: { Authorization: `Bearer ${authStore.token}` } 
      });
      return response.data;
    } catch (err: any) {
      error.value = `Failed to check course conflict: ${err.response?.data?.detail || err.message}`;
      console.error(error.value);
      throw err;
    } finally {
      loading.value = false;
    }
  };

  return {
    availableCourses,
    selectedCourses,
    courseDetail,
    schedule,
    stats,
    queueStatus,
    loading,
    error,
    fetchAvailableCourses,
    fetchSelectedCourses,
    fetchCourseDetail,
    selectCourse,
    deselectCourse,
    fetchSchedule,
    fetchStats,
    fetchQueueStatus,
    checkCourseConflict,
  };
});

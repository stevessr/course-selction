import { defineStore } from 'pinia';
import { ref } from 'vue';
import { teacherApi } from '@/services/api';
import { useAuthStore } from './auth';

interface Course {
  course_id: number;
  course_name: string;
  course_credit: number;
  course_type: string;
  course_time_begin: number;
  course_time_end: number;
  course_location: string;
  course_capacity: number;
  course_selected: number;
  course_left: number;
}

interface Student {
  student_id: number;
  student_name: string;
}

interface CourseDetail extends Course {
  students: Student[];
}

interface TeacherStats {
  total_courses: number;
  total_students: number;
  courses_by_type: { [key: string]: number };
}

export const useTeacherStore = defineStore('teacher', () => {
  const courses = ref<Course[]>([]);
  const courseDetail = ref<CourseDetail | null>(null);
  const stats = ref<TeacherStats | null>(null);

  const loading = ref(false);
  const error = ref<string | null>(null);

  const authStore = useAuthStore();

  const fetchCourses = async () => {
    if (!authStore.token) return;
    loading.value = true;
    error.value = null;
    try {
      const response = await teacherApi.get('/teacher/courses', {
        headers: { Authorization: `Bearer ${authStore.token}` }
      });
      courses.value = response.data.courses;
    } catch (err: any) {
      error.value = `Failed to fetch teacher courses: ${err.response?.data?.detail || err.message}`;
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
      const response = await teacherApi.post('/teacher/course/detail', 
        { course_id: courseId }, 
        { headers: { Authorization: `Bearer ${authStore.token}` } 
      });
      courseDetail.value = response.data;
    } catch (err: any) {
      error.value = `Failed to fetch teacher course detail: ${err.response?.data?.detail || err.message}`;
      console.error(error.value);
    } finally {
      loading.value = false;
    }
  };

  const updateCourse = async (course: Partial<Course>) => {
    if (!authStore.token) return;
    loading.value = true;
    error.value = null;
    try {
      const response = await teacherApi.post('/teacher/course/update', 
        course, 
        { headers: { Authorization: `Bearer ${authStore.token}` } 
      });
      await fetchCourses(); // Refresh courses list
      if (course.course_id) {
        await fetchCourseDetail(course.course_id); // Refresh detail if currently viewed
      }
      return response.data;
    } catch (err: any) {
      error.value = `Failed to update course: ${err.response?.data?.detail || err.message}`;
      console.error(error.value);
      throw err;
    } finally {
      loading.value = false;
    }
  };

  const createCourse = async (course: Omit<Course, 'course_id' | 'course_selected' | 'course_left'>) => {
    if (!authStore.token) return;
    loading.value = true;
    error.value = null;
    try {
      const response = await teacherApi.post('/teacher/course/create', 
        course, 
        { headers: { Authorization: `Bearer ${authStore.token}` } 
      });
      await fetchCourses(); // Refresh courses list
      return response.data;
    } catch (err: any) {
      error.value = `Failed to create course: ${err.response?.data?.detail || err.message}`;
      console.error(error.value);
      throw err;
    } finally {
      loading.value = false;
    }
  };

  const deleteCourse = async (courseId: number) => {
    if (!authStore.token) return;
    loading.value = true;
    error.value = null;
    try {
      const response = await teacherApi.post('/teacher/course/delete', 
        { course_id: courseId }, 
        { headers: { Authorization: `Bearer ${authStore.token}` } 
      });
      await fetchCourses(); // Refresh courses list
      return response.data;
    } catch (err: any) {
      error.value = `Failed to delete course: ${err.response?.data?.detail || err.message}`;
      console.error(error.value);
      throw err;
    } finally {
      loading.value = false;
    }
  };

  const removeStudentFromCourse = async (courseId: number, studentId: number) => {
    if (!authStore.token) return;
    loading.value = true;
    error.value = null;
    try {
      const response = await teacherApi.post('/teacher/student/remove', 
        { course_id: courseId, student_id: studentId }, 
        { headers: { Authorization: `Bearer ${authStore.token}` } 
      });
      await fetchCourseDetail(courseId); // Refresh course detail
      return response.data;
    } catch (err: any) {
      error.value = `Failed to remove student: ${err.response?.data?.detail || err.message}`;
      console.error(error.value);
      throw err;
    } finally {
      loading.value = false;
    }
  };

  const fetchStats = async () => {
    if (!authStore.token) return;
    loading.value = true;
    error.value = null;
    try {
      const response = await teacherApi.post('/teacher/stats', 
        {}, 
        { headers: { Authorization: `Bearer ${authStore.token}` } 
      });
      stats.value = response.data;
    } catch (err: any) {
      error.value = `Failed to fetch teacher stats: ${err.response?.data?.detail || err.message}`;
      console.error(error.value);
    } finally {
      loading.value = false;
    }
  };

  return {
    courses,
    courseDetail,
    stats,
    loading,
    error,
    fetchCourses,
    fetchCourseDetail,
    updateCourse,
    createCourse,
    deleteCourse,
    removeStudentFromCourse,
    fetchStats,
  };
});

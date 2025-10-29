<template>
  <div v-if="store.courseDetail">
    <h1>{{ store.courseDetail.course_name }}</h1>
    <p><strong>Credit:</strong> {{ store.courseDetail.course_credit }}</p>
    <p><strong>Teacher:</strong> {{ store.courseDetail.teacher_name }}</p>
    <p><strong>Location:</strong> {{ store.courseDetail.course_location }}</p>
    <p><strong>Capacity:</strong> {{ store.courseDetail.course_capacity }}</p>
    <p><strong>Selected:</strong> {{ store.courseDetail.course_selected }}</p>
    <p><strong>Is Selected:</strong> {{ store.courseDetail.is_selected ? 'Yes' : 'No' }}</p>
    <router-link :to="{ name: 'StudentDashboard' }">Back to Dashboard</router-link>
  </div>
  <div v-else>
    <p>Loading course details...</p>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useStudentStore } from '@/stores/student';

const store = useStudentStore();
const route = useRoute();

onMounted(() => {
  const courseId = Number(route.params.id);
  if (courseId) {
    store.fetchCourseDetail(courseId);
  }
});
</script>

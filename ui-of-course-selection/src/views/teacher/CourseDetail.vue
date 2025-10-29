<template>
  <div v-if="store.courseDetail">
    <h1>{{ store.courseDetail.course_name }}</h1>
    <p><strong>Credit:</strong> {{ store.courseDetail.course_credit }}</p>
    <p><strong>Location:</strong> {{ store.courseDetail.course_location }}</p>
    <p><strong>Capacity:</strong> {{ store.courseDetail.course_capacity }}</p>
    <p><strong>Selected:</strong> {{ store.courseDetail.course_selected }}</p>
    
    <h2>Enrolled Students</h2>
    <ul v-if="store.courseDetail.students && store.courseDetail.students.length > 0">
      <li v-for="student in store.courseDetail.students" :key="student.student_id">
        {{ student.student_name }} (ID: {{ student.student_id }})
      </li>
    </ul>
    <p v-else>No students enrolled in this course.</p>

    <router-link :to="{ name: 'TeacherDashboard' }">Back to Dashboard</router-link>
  </div>
  <div v-else>
    <p>Loading course details...</p>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useTeacherStore } from '@/stores/teacher';

const store = useTeacherStore();
const route = useRoute();

onMounted(() => {
  const courseId = Number(route.params.id);
  if (courseId) {
    store.fetchCourseDetail(courseId);
  }
});
</script>

<style scoped>
ul {
  list-style-type: none;
  padding: 0;
}
li {
  border: 1px solid #ccc;
  padding: 1rem;
  margin-bottom: 1rem;
  border-radius: 4px;
}
</style>

<template>
  <div>
    <h2>My Courses</h2>
    <div v-if="store.courses.length === 0">You have no courses.</div>
    <ul v-else>
      <li v-for="course in store.courses" :key="course.course_id">
        <h3>{{ course.course_name }}</h3>
        <p>Credit: {{ course.course_credit }}</p>
        <p>Capacity: {{ course.course_capacity }}</p>
        <p>Selected: {{ course.course_selected }}</p>
        <router-link :to="{ name: 'TeacherCourseDetail', params: { id: course.course_id } }">
          <button>Details</button>
        </router-link>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useTeacherStore } from '@/stores/teacher';

const store = useTeacherStore();

onMounted(() => {
  store.fetchCourses();
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

<template>
  <div>
    <h2>Selected Courses</h2>
    <div v-if="store.selectedCourses.length === 0">No courses selected.</div>
    <ul v-else>
      <li v-for="course in store.selectedCourses" :key="course.course_id">
        <h3>{{ course.course_name }}</h3>
        <p>Credit: {{ course.course_credit }}</p>
        <p>Teacher: {{ course.teacher_name }}</p>
        <button @click="deselectCourse(course.course_id)">Deselect</button>
        <router-link :to="{ name: 'StudentCourseDetail', params: { id: course.course_id } }">
          <button>Details</button>
        </router-link>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useStudentStore } from '@/stores/student';

const store = useStudentStore();

onMounted(() => {
  store.fetchSelectedCourses();
});

const deselectCourse = (courseId: number) => {
  store.deselectCourse(courseId);
};
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
button {
  margin-right: 0.5rem;
}
</style>

<template>
  <div>
    <h2>Available Courses</h2>
    <div v-if="store.availableCourses.length === 0">No courses available.</div>
    <ul v-else>
      <li v-for="course in store.availableCourses" :key="course.course_id">
        <h3>{{ course.course_name }}</h3>
        <p>Credit: {{ course.course_credit }}</p>
        <p>Teacher: {{ course.teacher_name }}</p>
        <p>Location: {{ course.course_location }}</p>
        <p>Capacity: {{ course.course_capacity }}</p>
        <p>Selected: {{ course.course_selected }}</p>
        <button @click="selectCourse(course.course_id)">Select</button>
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
  store.fetchAvailableCourses();
});

const selectCourse = (courseId: number) => {
  store.selectCourse(courseId);
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

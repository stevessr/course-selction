<template>
  <a-card v-if="store.courseDetail" :title="store.courseDetail.course_name">
    <a-descriptions bordered :column="1">
      <a-descriptions-item label="Credit">{{ store.courseDetail.course_credit }}</a-descriptions-item>
      <a-descriptions-item label="Teacher">{{ store.courseDetail.teacher_name }}</a-descriptions-item>
      <a-descriptions-item label="Location">{{ store.courseDetail.course_location }}</a-descriptions-item>
      <a-descriptions-item label="Capacity">{{ store.courseDetail.course_capacity }}</a-descriptions-item>
      <a-descriptions-item label="Selected">{{ store.courseDetail.course_selected }}</a-descriptions-item>
      <a-descriptions-item label="Is Selected">{{ store.courseDetail.is_selected ? 'Yes' : 'No' }}</a-descriptions-item>
    </a-descriptions>
  </a-card>
  <a-alert v-else-if="store.error" :message="store.error" type="error" show-icon />
  <div v-else>
    <a-spin tip="Loading course details..."></a-spin>
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

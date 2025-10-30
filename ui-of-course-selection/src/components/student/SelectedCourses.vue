<template>
  <a-card title="Selected Courses">
    <a-alert v-if="store.error" :message="store.error" type="error" show-icon style="margin-bottom: 16px" />
    <a-list :data-source="store.selectedCourses" :loading="store.loading">
      <template #renderItem="{ item }">
        <a-list-item>
          <a-list-item-meta
            :title="item.course_name"
            :description="`Credit: ${item.course_credit} | Teacher: ${item.teacher_name}`"
          />
          <template #actions>
            <a-button type="danger" @click="deselectCourse(item.course_id)" :loading="store.loading">Deselect</a-button>
            <router-link :to="{ name: 'StudentCourseDetail', params: { id: item.course_id } }">
              <a-button>Details</a-button>
            </router-link>
          </template>
        </a-list-item>
      </template>
    </a-list>
  </a-card>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useStudentStore } from '@/stores/student';
import { message } from 'ant-design-vue';

const store = useStudentStore();

onMounted(() => {
  store.fetchSelectedCourses();
});

const deselectCourse = async (courseId: number) => {
  try {
    const result = await store.deselectCourse(courseId);
    message.success(`Course deselection queued. Task ID: ${result.queue_id}`);
  } catch (error) {
    message.error(store.error || 'Failed to deselect course.');
  }
};
</script>

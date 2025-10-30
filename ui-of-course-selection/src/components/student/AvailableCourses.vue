<template>
  <a-card title="Available Courses">
    <a-alert v-if="store.error" :message="store.error" type="error" show-icon style="margin-bottom: 16px" />
    <a-list :data-source="store.availableCourses" :loading="store.loading">
      <template #renderItem="{ item }">
        <a-list-item>
          <a-list-item-meta
            :title="item.course_name"
            :description="`Credit: ${item.course_credit} | Teacher: ${item.teacher_name}`"
          />
          <div>
            <p>Location: {{ item.course_location }}</p>
            <p>Capacity: {{ item.course_capacity }}</p>
            <p>Selected: {{ item.course_selected }}</p>
          </div>
          <template #actions>
            <a-button type="primary" @click="selectCourse(item.course_id)" :loading="store.loading">Select</a-button>
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
  store.fetchAvailableCourses();
});

const selectCourse = async (courseId: number) => {
  try {
    const result = await store.selectCourse(courseId);
    message.success(`Course selection queued. Task ID: ${result.queue_id}`);
  } catch (error) {
    message.error(store.error || 'Failed to select course.');
  }
};
</script>

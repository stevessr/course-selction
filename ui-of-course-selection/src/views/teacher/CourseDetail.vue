<template>
  <a-card v-if="store.courseDetail" :title="store.courseDetail.course_name">
    <a-alert v-if="store.error" :message="store.error" type="error" show-icon style="margin-bottom: 16px" />
    <a-descriptions bordered :column="1">
      <a-descriptions-item label="Credit">{{ store.courseDetail.course_credit }}</a-descriptions-item>
      <a-descriptions-item label="Location">{{ store.courseDetail.course_location }}</a-descriptions-item>
      <a-descriptions-item label="Capacity">{{ store.courseDetail.course_capacity }}</a-descriptions-item>
      <a-descriptions-item label="Selected">{{ store.courseDetail.course_selected }}</a-descriptions-item>
    </a-descriptions>

    <a-divider />

    <h2>Enrolled Students</h2>
    <a-list
      v-if="store.courseDetail.students && store.courseDetail.students.length > 0"
      :data-source="store.courseDetail.students"
      bordered
      :loading="store.loading"
    >
      <template #renderItem="{ item }">
        <a-list-item>
          {{ item.student_name }} (ID: {{ item.student_id }})
          <template #actions>
            <a-popconfirm
              title="Are you sure remove this student from course?"
              ok-text="Yes"
              cancel-text="No"
              @confirm="handleRemoveStudent(item.student_id)"
            >
              <a-button type="danger" size="small">Remove</a-button>
            </a-popconfirm>
          </template>
        </a-list-item>
      </template>
    </a-list>
    <a-empty v-else description="No students enrolled in this course." />
  </a-card>
  <a-alert v-else-if="store.error" :message="store.error" type="error" show-icon />
  <div v-else>
    <a-spin tip="Loading course details..."></a-spin>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useTeacherStore } from '@/stores/teacher';
import { message } from 'ant-design-vue';

const store = useTeacherStore();
const route = useRoute();

const courseId = Number(route.params.id);

onMounted(() => {
  if (courseId) {
    store.fetchCourseDetail(courseId);
  }
});

const handleRemoveStudent = async (studentId: number) => {
  try {
    await store.removeStudentFromCourse(courseId, studentId);
    message.success('Student removed successfully!');
  } catch (error) {
    message.error(store.error || 'Failed to remove student.');
  }
};
</script>

<template>
  <a-card title="My Courses">
    <template #extra>
      <a-button type="primary" @click="showCreateCourseModal = true">
        <template #icon><plus-outlined /></template>
        Create Course
      </a-button>
    </template>
    <a-alert v-if="store.error" :message="store.error" type="error" show-icon style="margin-bottom: 16px" />
    <a-list :data-source="store.courses" :loading="store.loading">
      <template #renderItem="{ item }">
        <a-list-item>
          <a-list-item-meta
            :title="item.course_name"
            :description="`Credit: ${item.course_credit}`"
          />
          <div>
            <p>Capacity: {{ item.course_capacity }}</p>
            <p>Selected: {{ item.course_selected }}</p>
          </div>
          <template #actions>
            <a-button @click="openUpdateCourseModal(item)">
              <template #icon><edit-outlined /></template>
              Edit
            </a-button>
            <a-popconfirm
              title="Are you sure delete this course?"
              ok-text="Yes"
              cancel-text="No"
              @confirm="handleDeleteCourse(item.course_id)"
            >
              <a-button type="danger">
                <template #icon><delete-outlined /></template>
                Delete
              </a-button>
            </a-popconfirm>
            <router-link :to="{ name: 'TeacherCourseDetail', params: { id: item.course_id } }">
              <a-button>Details</a-button>
            </router-link>
          </template>
        </a-list-item>
      </template>
    </a-list>

    <!-- Create Course Modal -->
    <a-modal
      v-model:open="showCreateCourseModal"
      title="Create New Course"
      @ok="handleCreateCourse"
      :confirm-loading="store.loading"
    >
      <a-form :model="newCourse" layout="vertical">
        <a-form-item label="Course Name">
          <a-input v-model:value="newCourse.course_name" />
        </a-form-item>
        <a-form-item label="Credit">
          <a-input-number v-model:value="newCourse.course_credit" :min="1" />
        </a-form-item>
        <a-form-item label="Type">
          <a-input v-model:value="newCourse.course_type" />
        </a-form-item>
        <a-form-item label="Time Begin">
          <a-input-number v-model:value="newCourse.course_time_begin" :min="0" :max="23" />
        </a-form-item>
        <a-form-item label="Time End">
          <a-input-number v-model:value="newCourse.course_time_end" :min="0" :max="23" />
        </a-form-item>
        <a-form-item label="Location">
          <a-input v-model:value="newCourse.course_location" />
        </a-form-item>
        <a-form-item label="Capacity">
          <a-input-number v-model:value="newCourse.course_capacity" :min="1" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Update Course Modal -->
    <a-modal
      v-model:open="showUpdateCourseModal"
      title="Update Course"
      @ok="handleUpdateCourse"
      :confirm-loading="store.loading"
    >
      <a-form :model="currentCourse" layout="vertical">
        <a-form-item label="Course Name">
          <a-input v-model:value="currentCourse.course_name" />
        </a-form-item>
        <a-form-item label="Credit">
          <a-input-number v-model:value="currentCourse.course_credit" :min="1" />
        </a-form-item>
        <a-form-item label="Type">
          <a-input v-model:value="currentCourse.course_type" />
        </a-form-item>
        <a-form-item label="Time Begin">
          <a-input-number v-model:value="currentCourse.course_time_begin" :min="0" :max="23" />
        </a-form-item>
        <a-form-item label="Time End">
          <a-input-number v-model:value="currentCourse.course_time_end" :min="0" :max="23" />
        </a-form-item>
        <a-form-item label="Location">
          <a-input v-model:value="currentCourse.course_location" />
        </a-form-item>
        <a-form-item label="Capacity">
          <a-input-number v-model:value="currentCourse.course_capacity" :min="1" />
        </a-form-item>
      </a-form>
    </a-modal>
  </a-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useTeacherStore } from '@/stores/teacher';
import { message } from 'ant-design-vue';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
} from '@ant-design/icons-vue';

const store = useTeacherStore();

const showCreateCourseModal = ref(false);
const showUpdateCourseModal = ref(false);
const newCourse = ref({
  course_name: '',
  course_credit: 1,
  course_type: '',
  course_time_begin: 0,
  course_time_end: 0,
  course_location: '',
  course_capacity: 1,
});
const currentCourse = ref<any>(null);

onMounted(() => {
  store.fetchCourses();
});

const handleCreateCourse = async () => {
  try {
    await store.createCourse(newCourse.value);
    message.success('Course created successfully!');
    showCreateCourseModal.value = false;
    newCourse.value = {
      course_name: '',
      course_credit: 1,
      course_type: '',
      course_time_begin: 0,
      course_time_end: 0,
      course_location: '',
      course_capacity: 1,
    };
  } catch (error) {
    message.error(store.error || 'Failed to create course.');
  }
};

const openUpdateCourseModal = (course: any) => {
  currentCourse.value = { ...course };
  showUpdateCourseModal.value = true;
};

const handleUpdateCourse = async () => {
  try {
    await store.updateCourse(currentCourse.value);
    message.success('Course updated successfully!');
    showUpdateCourseModal.value = false;
  } catch (error) {
    message.error(store.error || 'Failed to update course.');
  }
};

const handleDeleteCourse = async (courseId: number) => {
  try {
    await store.deleteCourse(courseId);
    message.success('Course deleted successfully!');
  } catch (error) {
    message.error(store.error || 'Failed to delete course.');
  }
};
</script>

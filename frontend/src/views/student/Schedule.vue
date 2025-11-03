<template>
  <div>
    <h1>{{ t("student.mySchedule") }}</h1>

    <a-button
      @click="loadSchedule"
      :loading="loading"
      style="margin-bottom: 16px"
    >
      {{ t("common.refresh") }}
    </a-button>

    <a-card v-if="!loading && schedule" style="margin-top: 16px">
      <a-row :gutter="[16, 16]">
        <a-col
          v-for="day in [1, 2, 3, 4, 5, 6, 7]"
          :key="day"
          :span="24"
          :md="12"
          :lg="8"
        >
          <a-card :title="getDayName(day)" size="small">
            <div v-if="schedule[day] && schedule[day].length > 0">
              <a-list size="small" :data-source="schedule[day]">
                <template #renderItem="{ item }">
                  <a-list-item
                    style="cursor: pointer"
                    @click="showCourseDetail(item)"
                  >
                    <a-list-item-meta>
                      <template #title>{{ item.course_name }}</template>
                      <template #description>
                        <div>{{ item.course_location }}</div>
                        <div>
                          {{ t("course.time") }}:
                          {{ formatTime(item.course_time_begin) }} -
                          {{ formatTime(item.course_time_end) }}
                        </div>
                      </template>
                    </a-list-item-meta>
                  </a-list-item>
                </template>
              </a-list>
            </div>
            <a-empty v-else :description="t('student.noClasses')" />
          </a-card>
        </a-col>
      </a-row>
    </a-card>

    <a-empty
      v-if="!loading && !schedule"
      :description="t('student.noSchedule')"
    />

    <a-modal
      v-model:open="detailModalVisible"
      :title="t('course.courseDetails')"
      :footer="null"
      width="600px"
    >
      <a-descriptions v-if="selectedCourse" :column="1" bordered>
        <a-descriptions-item :label="t('course.courseName')">
          {{ selectedCourse.course_name }}
        </a-descriptions-item>
        <a-descriptions-item :label="t('course.credits')">
          {{ selectedCourse.course_credit }}
        </a-descriptions-item>
        <a-descriptions-item :label="t('course.type')">
          {{ selectedCourse.course_type }}
        </a-descriptions-item>
        <a-descriptions-item :label="t('course.location')">
          {{ selectedCourse.course_location }}
        </a-descriptions-item>
        <a-descriptions-item :label="t('course.time')">
          {{ formatTime(selectedCourse.course_time_begin) }} -
          {{ formatTime(selectedCourse.course_time_end) }}
        </a-descriptions-item>
        <a-descriptions-item :label="t('student.day')">
          {{ getDayName(selectedCourse.course_day) }}
        </a-descriptions-item>
        <a-descriptions-item
          :label="t('course.capacity')"
          v-if="selectedCourse.course_capacity"
        >
          {{ selectedCourse.course_selected }} /
          {{ selectedCourse.course_capacity }}
        </a-descriptions-item>
        <a-descriptions-item
          :label="t('course.availableSeats')"
          v-if="selectedCourse.course_left !== undefined"
        >
          <a-tag
            :color="
              selectedCourse.course_left > 10
                ? 'green'
                : selectedCourse.course_left > 0
                ? 'orange'
                : 'red'
            "
          >
            {{ selectedCourse.course_left }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item
          :label="t('course.tags')"
          v-if="
            selectedCourse.course_tags && selectedCourse.course_tags.length > 0
          "
        >
          <a-tag
            v-for="tag in selectedCourse.course_tags"
            :key="tag"
            color="blue"
            >{{ tag }}</a-tag
          >
        </a-descriptions-item>
        <a-descriptions-item
          :label="t('course.notes')"
          v-if="selectedCourse.course_notes"
        >
          {{ selectedCourse.course_notes }}
        </a-descriptions-item>
      </a-descriptions>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { message } from "ant-design-vue";
import { useI18n } from "vue-i18n";
import { useAuthStore } from "@/store/auth";
import studentApi from "@/api/student";

const { t } = useI18n();

const authStore = useAuthStore();

const loading = ref(false);
const schedule = ref(null);
const detailModalVisible = ref(false);
const selectedCourse = ref(null);

const dayNames = [
  "",
  t("course.monday"),
  t("course.tuesday"),
  t("course.wednesday"),
  t("course.thursday"),
  t("course.friday"),
  t("course.saturday"),
  t("course.sunday"),
];

const getDayName = (day) =>
  typeof dayNames[day] === "function" ? dayNames[day].value : dayNames[day];

const formatTime = (time) => {
  if (!time) return "";
  const timeStr = String(time).padStart(4, "0");
  const hours = timeStr.slice(0, 2);
  const minutes = timeStr.slice(2, 4);
  return `${hours}:${minutes}`;
};

const loadSchedule = async () => {
  loading.value = true;
  try {
    const response = await studentApi.getSchedule(
      authStore.accessToken?.value || authStore.accessToken
    );
    schedule.value = response.schedule;
  } catch (error) {
    message.error(error.message || t("student.loadScheduleFailed"));
  } finally {
    loading.value = false;
  }
};

const showCourseDetail = async (course) => {
  try {
    const detail = await studentApi.getCourseDetail(
      authStore.accessToken?.value || authStore.accessToken,
      course.course_id
    );
    selectedCourse.value = detail;
    detailModalVisible.value = true;
  } catch (error) {
    message.error(error.message || t("message.loadCourseDetailsError"));
  }
};

onMounted(() => {
  loadSchedule();
});
</script>

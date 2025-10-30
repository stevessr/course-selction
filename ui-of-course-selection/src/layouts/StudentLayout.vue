<template>
  <a-layout style="min-height: 100vh">
    <a-layout-sider collapsible>
      <div class="logo" />
      <a-menu theme="dark" mode="inline" :selected-keys="[$route.name]">
        <a-menu-item key="StudentDashboard">
          <router-link :to="{ name: 'StudentDashboard' }">
            <pie-chart-outlined />
            <span>Dashboard</span>
          </router-link>
        </a-menu-item>
      </a-menu>
    </a-layout-sider>
    <a-layout>
      <a-layout-header style="background: #fff; padding: 0">
        <a-button @click="handleLogout" style="float: right; margin: 16px">
          Logout
        </a-button>
      </a-layout-header>
      <a-layout-content style="margin: 0 16px">
        <a-breadcrumb style="margin: 16px 0">
          <a-breadcrumb-item>Student</a-breadcrumb-item>
          <a-breadcrumb-item>{{ $route.name }}</a-breadcrumb-item>
        </a-breadcrumb>
        <div :style="{ padding: '24px', background: '#fff', minHeight: '360px' }">
          <router-view />
        </div>
      </a-layout-content>
      <a-layout-footer style="text-align: center">
        Course Selection System ©2025 Created by Gemini
      </a-layout-footer>
    </a-layout>
  </a-layout>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import {
  PieChartOutlined,
} from '@ant-design/icons-vue';

const router = useRouter();
const authStore = useAuthStore();

const handleLogout = () => {
  authStore.clearAuth();
  router.push({ name: 'Login' });
};
</script>

<style scoped>
.logo {
  height: 32px;
  background: rgba(255, 255, 255, 0.2);
  margin: 16px;
}
</style>

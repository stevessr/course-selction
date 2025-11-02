<template>
  <a-layout style="min-height: 100vh">
    <a-layout-header style="background: #001529; padding: 0">
      <div style="display: flex; justify-content: space-between; align-items: center; padding: 0 24px">
        <div style="color: white; font-size: 20px; font-weight: bold">
          Course Selection - Student
        </div>
        <a-space>
          <span style="color: white">{{ authStore.username }}</span>
          <a-button type="primary" @click="handleLogout">Logout</a-button>
        </a-space>
      </div>
    </a-layout-header>
    
    <a-layout>
      <a-layout-sider width="200" style="background: #fff">
        <a-menu
          v-model:selectedKeys="selectedKeys"
          mode="inline"
          style="height: 100%; border-right: 0"
        >
          <a-menu-item key="courses" @click="$router.push('/student/courses')">
            <span>Available Courses</span>
          </a-menu-item>
          <a-menu-item key="selected" @click="$router.push('/student/selected')">
            <span>My Courses</span>
          </a-menu-item>
          <a-menu-item key="schedule" @click="$router.push('/student/schedule')">
            <span>Schedule</span>
          </a-menu-item>
          <a-menu-item key="settings" @click="$router.push('/student/settings')">
            <span>Settings</span>
          </a-menu-item>
        </a-menu>
      </a-layout-sider>
      
      <a-layout-content style="padding: 24px; background: #fff">
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const selectedKeys = ref(['courses'])

watch(() => route.path, (path) => {
  if (path.includes('courses')) selectedKeys.value = ['courses']
  else if (path.includes('selected')) selectedKeys.value = ['selected']
  else if (path.includes('schedule')) selectedKeys.value = ['schedule']
  else if (path.includes('settings')) selectedKeys.value = ['settings']
})

const handleLogout = async () => {
  await authStore.logout()
  message.success('Logged out successfully')
  router.push('/login')
}
</script>

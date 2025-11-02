<template>
  <a-layout style="min-height: 100vh">
    <a-layout-header style="background: #001529; padding: 0">
      <div style="display: flex; justify-content: space-between; align-items: center; padding: 0 24px">
        <div style="color: white; font-size: 20px; font-weight: bold">
          Admin Panel
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
          <a-menu-item key="users" @click="$router.push('/admin/users')">
            User Management
          </a-menu-item>
          <a-menu-item key="courses" @click="$router.push('/admin/courses')">
            Course Management
          </a-menu-item>
          <a-menu-item key="tags" @click="$router.push('/admin/tags')">
            Tag Management
          </a-menu-item>
          <a-menu-item key="codes" @click="$router.push('/admin/codes')">
            Registration Codes
          </a-menu-item>
          <a-menu-item key="reset-codes" @click="$router.push('/admin/reset-codes')">
            Reset Codes
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
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const authStore = useAuthStore()
const selectedKeys = ref(['users'])

const handleLogout = async () => {
  await authStore.logout()
  message.success('Logged out successfully')
  router.push('/login')
}
</script>

<template>
  <a-layout style="min-height: 100vh">
    <a-layout-header style="background: #001529; padding: 0">
      <div style="display: flex; justify-content: space-between; align-items: center; padding: 0 24px">
        <div style="color: white; font-size: 20px; font-weight: bold">
          {{ t('nav.teacher') }} - {{ t('admin.courseManagement') }}
        </div>
        <a-space>
          <LanguageSwitcher />
          <span style="color: white">{{ authStore.username }}</span>
          <a-button type="primary" @click="handleLogout">{{ t('nav.logout') }}</a-button>
        </a-space>
      </div>
    </a-layout-header>
    
    <a-layout>
      <a-layout-sider width="200" :style="{ background: themeStore.isDark ? '#1f1f1f' : '#fff' }">
        <a-menu
          v-model:selectedKeys="selectedKeys"
          mode="inline"
          style="height: 100%; border-right: 0"
        >
          <a-menu-item key="courses" @click="$router.push('/teacher/courses')">
            {{ t('teacher.myCourses') }}
          </a-menu-item>
          <a-menu-item key="create" @click="$router.push('/teacher/create')">
            {{ t('teacher.createNewCourse') }}
          </a-menu-item>
          <a-menu-item key="settings" @click="$router.push('/teacher/settings')">
            {{ t('nav.settings') }}
          </a-menu-item>
        </a-menu>
      </a-layout-sider>
      
      <a-layout-content :style="{ padding: '24px', background: themeStore.isDark ? '#141414' : '#fff' }">
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/store/auth'
import { useThemeStore } from '@/store/theme'
import LanguageSwitcher from '@/components/LanguageSwitcher.vue'

const { t } = useI18n()

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const themeStore = useThemeStore()
const selectedKeys = ref(['courses'])

watch(() => route.path, (path) => {
  if (path.includes('courses')) selectedKeys.value = ['courses']
  else if (path.includes('create') || path.includes('edit')) selectedKeys.value = ['create']
  else if (path.includes('settings')) selectedKeys.value = ['settings']
})

const handleLogout = async () => {
  await authStore.logout()
  message.success(t('common.success'))
  router.push('/login')
}
</script>

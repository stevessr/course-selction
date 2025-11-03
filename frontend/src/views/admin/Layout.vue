<template>
  <a-layout style="min-height: 100vh">
    <a-layout-header style="background: #001529; padding: 0">
      <div style="display: flex; justify-content: space-between; align-items: center; padding: 0 24px">
        <div style="color: white; font-size: 20px; font-weight: bold">
          {{ t('user.admin') }}
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
          <a-menu-item key="users" @click="$router.push('/admin/users')">
            {{ t('admin.userManagement') }}
          </a-menu-item>
          <a-menu-item key="courses" @click="$router.push('/admin/courses')">
            {{ t('admin.courseManagement') }}
          </a-menu-item>
          <a-menu-item key="tags" @click="$router.push('/admin/tags')">
            {{ t('admin.tagManagement') }}
          </a-menu-item>
          <a-menu-item key="codes" @click="$router.push('/admin/codes')">
            {{ t('nav.registrationCodes') }}
          </a-menu-item>
          <a-menu-item key="reset-codes" @click="$router.push('/admin/reset-codes')">
            {{ t('nav.resetCodes') }}
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
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/store/auth'
import { useThemeStore } from '@/store/theme'
import LanguageSwitcher from '@/components/LanguageSwitcher.vue'

const { t } = useI18n()

const router = useRouter()
const authStore = useAuthStore()
const themeStore = useThemeStore()
const selectedKeys = ref(['users'])

const handleLogout = async () => {
  await authStore.logout()
  message.success(t('common.success'))
  router.push('/login')
}
</script>

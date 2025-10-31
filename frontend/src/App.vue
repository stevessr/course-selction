<template>
  <a-config-provider :theme="{ token: { colorPrimary: '#1890ff' } }">
    <router-view />
  </a-config-provider>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from '@/store/auth'

const authStore = useAuthStore()

onMounted(() => {
  // Try to restore session from localStorage
  authStore.restoreSession()
})
</script>

<style>
#app {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
</style>

<template>
  <a-config-provider :theme="{ token: { colorPrimary: '#1890ff' } }">
    <router-view />
    <DebugPanel />
  </a-config-provider>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from '@/store/auth'
import { useDebugStore } from '@/store/debug'
import DebugPanel from '@/components/DebugPanel.vue'

const authStore = useAuthStore()
const debugStore = useDebugStore()

onMounted(() => {
  // Try to restore session from localStorage
  authStore.restoreSession()
  
  // Check if debug mode should be enabled
  debugStore.checkDebugMode()
  
  // Add keyboard shortcut to toggle debug panel (Ctrl+Shift+D)
  window.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.shiftKey && e.key === 'D') {
      debugStore.toggle()
    }
  })
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

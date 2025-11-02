<template>
  <a-config-provider :theme="themeConfig">
    <router-view />
    <ThemeToggle />
    <DebugPanel />
    <DebugFloatingButton />
  </a-config-provider>
</template>

<script setup>
import { onMounted, computed } from 'vue'
import { theme } from 'ant-design-vue'
import { useAuthStore } from '@/store/auth'
import { useDebugStore } from '@/store/debug'
import { useThemeStore } from '@/store/theme'
import ThemeToggle from '@/components/ThemeToggle.vue'
import DebugPanel from '@/components/DebugPanel.vue'
import DebugFloatingButton from '@/components/DebugFloatingButton.vue'

const authStore = useAuthStore()
const debugStore = useDebugStore()
const themeStore = useThemeStore()

// Configure Ant Design theme based on current theme
const themeConfig = computed(() => {
  if (themeStore.isDark) {
    return {
      algorithm: theme.darkAlgorithm,
      token: {
        colorPrimary: '#1890ff',
      }
    }
  }
  return {
    algorithm: theme.defaultAlgorithm,
    token: {
      colorPrimary: '#1890ff',
    }
  }
})

onMounted(() => {
  // Try to restore session from localStorage
  authStore.restoreSession()
  
  // Check if debug mode should be enabled
  debugStore.checkDebugMode()
  
  // Add keyboard shortcut to toggle debug panel (Ctrl+Shift+D) - for power users
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
  min-height: 100vh;
  transition: background-color 0.3s ease, color 0.3s ease;
}

/* Light theme (default) */
:root[data-theme="light"] {
  --bg-color: #ffffff;
  --text-color: #000000;
}

/* Dark theme */
:root[data-theme="dark"] {
  --bg-color: #141414;
  --text-color: #ffffff;
}

:root[data-theme="dark"] #app {
  background-color: var(--bg-color);
  color: var(--text-color);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
</style>

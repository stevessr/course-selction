<template>
  <a-tooltip :title="isDark ? '切换到浅色模式 / Switch to Light Mode' : '切换到深色模式 / Switch to Dark Mode'" placement="left">
    <a-button
      type="text"
      :icon="isDark ? h(SunOutlined) : h(MoonOutlined)"
      @click="toggleTheme"
      class="theme-toggle-button"
      size="large"
    />
  </a-tooltip>
</template>

<script setup>
import { h } from 'vue'
import { SunOutlined, MoonOutlined } from '@ant-design/icons-vue'
import { useThemeStore } from '@/store/theme'

const themeStore = useThemeStore()
const { isDark, toggleTheme } = themeStore
</script>

<style scoped>
.theme-toggle-button {
  position: fixed;
  bottom: 80px;
  right: 24px;
  z-index: 1000;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  transition: all 0.3s ease;
}

.theme-toggle-button:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
}
</style>

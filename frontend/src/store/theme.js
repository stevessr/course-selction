import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  // Get initial theme from localStorage or system preference
  const getInitialTheme = () => {
    const stored = localStorage.getItem('theme')
    if (stored) {
      return stored
    }
    // Check system preference
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark'
    }
    return 'light'
  }

  const theme = ref(getInitialTheme())

  const isDark = computed(() => theme.value === 'dark')

  const toggleTheme = () => {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
  }

  const setTheme = (newTheme) => {
    theme.value = newTheme
  }

  // Watch for theme changes and persist to localStorage
  watch(theme, (newTheme) => {
    localStorage.setItem('theme', newTheme)
    // Apply theme class to document
    document.documentElement.setAttribute('data-theme', newTheme)
  }, { immediate: true })

  // Listen for system theme changes
  if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      if (!localStorage.getItem('theme')) {
        setTheme(e.matches ? 'dark' : 'light')
      }
    })
  }

  return {
    theme,
    isDark,
    toggleTheme,
    setTheme
  }
})

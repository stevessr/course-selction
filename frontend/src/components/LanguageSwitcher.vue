<template>
  <a-dropdown>
    <a-button>
      <GlobalOutlined />
      {{ currentLanguage }}
    </a-button>
    <template #overlay>
      <a-menu @click="handleLanguageChange">
        <a-menu-item key="zh">
          中文
        </a-menu-item>
        <a-menu-item key="en">
          English
        </a-menu-item>
      </a-menu>
    </template>
  </a-dropdown>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { GlobalOutlined } from '@ant-design/icons-vue'

const { locale } = useI18n()

const currentLanguage = computed(() => {
  return locale.value === 'zh' ? '中文' : 'English'
})

const handleLanguageChange = ({ key }) => {
  locale.value = key
  localStorage.setItem('locale', key)
  // Reload to apply Ant Design locale
  window.location.reload()
}
</script>

<template>
  <div v-if="!debugStore.isEnabled" class="debug-floating-button" @click="openDebugPanel">
    <a-tooltip title="Open Debug Panel (Ctrl+Shift+D)" placement="left">
      <BugOutlined :style="{ fontSize: '24px', color: token.colorPrimary }" />
      <a-badge 
        v-if="debugStore.errors.length > 0" 
        :count="debugStore.errors.length" 
        :offset="[-5, 5]"
        :number-style="{ backgroundColor: token.colorError }"
      />
    </a-tooltip>
  </div>
</template>

<script setup>
import { BugOutlined } from '@ant-design/icons-vue'
import { useDebugStore } from '@/store/debug'
import { theme } from 'ant-design-vue'

const { useToken } = theme
const { token } = useToken()
const debugStore = useDebugStore()

const openDebugPanel = () => {
  debugStore.enable()
}
</script>

<style scoped>
.debug-floating-button {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: v-bind('token.colorBgContainer');
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 999;
  border: 1px solid v-bind('token.colorBorder');
}

.debug-floating-button:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
  background: v-bind('token.colorPrimaryBg');
}

.debug-floating-button:active {
  transform: scale(0.95);
}
</style>

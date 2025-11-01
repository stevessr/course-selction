<template>
  <div v-if="debugStore.isEnabled" class="debug-panel" :class="{ minimized: isMinimized }">
    <div class="debug-header" @click="toggleMinimize">
      <span class="debug-title">
        <BugOutlined />
        Debug Panel
        <a-badge :count="debugStore.errors.length" :offset="[5, 0]" />
      </span>
      <div class="debug-actions">
        <a-tooltip title="Clear all errors">
          <DeleteOutlined @click.stop="clearErrors" class="action-icon" />
        </a-tooltip>
        <a-tooltip :title="isMinimized ? 'Expand' : 'Minimize'">
          <component :is="isMinimized ? 'ExpandOutlined' : 'ShrinkOutlined'" class="action-icon" />
        </a-tooltip>
        <a-tooltip title="Close debug panel">
          <CloseOutlined @click.stop="closePanel" class="action-icon" />
        </a-tooltip>
      </div>
    </div>
    
    <div v-if="!isMinimized" class="debug-content">
      <a-tabs v-model:activeKey="activeTab">
        <a-tab-pane key="errors" tab="Errors">
          <div v-if="debugStore.errors.length === 0" class="empty-state">
            <CheckCircleOutlined style="font-size: 48px; color: #52c41a;" />
            <p>No errors detected</p>
          </div>
          <div v-else class="error-list">
            <div v-for="(error, index) in debugStore.errors" :key="index" class="error-item">
              <div class="error-header">
                <span class="error-type" :class="error.type">
                  {{ error.type.toUpperCase() }}
                </span>
                <span class="error-time">{{ formatTime(error.timestamp) }}</span>
                <DeleteOutlined @click="removeError(index)" class="delete-icon" />
              </div>
              <div class="error-message">{{ error.message }}</div>
              <div v-if="error.stack" class="error-stack">
                <a-collapse ghost>
                  <a-collapse-panel key="1" header="Stack Trace">
                    <pre>{{ error.stack }}</pre>
                  </a-collapse-panel>
                </a-collapse>
              </div>
              <div v-if="error.context" class="error-context">
                <a-collapse ghost>
                  <a-collapse-panel key="1" header="Context">
                    <pre>{{ JSON.stringify(error.context, null, 2) }}</pre>
                  </a-collapse-panel>
                </a-collapse>
              </div>
            </div>
          </div>
        </a-tab-pane>
        
        <a-tab-pane key="network" tab="Network">
          <div v-if="debugStore.networkErrors.length === 0" class="empty-state">
            <CheckCircleOutlined style="font-size: 48px; color: #52c41a;" />
            <p>No network errors</p>
          </div>
          <div v-else class="error-list">
            <div v-for="(error, index) in debugStore.networkErrors" :key="index" class="error-item">
              <div class="error-header">
                <span class="error-type network">
                  {{ error.method }} {{ error.status }}
                </span>
                <span class="error-time">{{ formatTime(error.timestamp) }}</span>
                <DeleteOutlined @click.stop="removeNetworkError(index)" class="delete-icon" />
              </div>
              <div class="error-message">{{ error.url }}</div>
              <div v-if="error.response" class="error-context">
                <a-collapse ghost>
                  <a-collapse-panel key="1" header="Response">
                    <pre>{{ JSON.stringify(error.response, null, 2) }}</pre>
                  </a-collapse-panel>
                </a-collapse>
              </div>
            </div>
          </div>
        </a-tab-pane>
        
        <a-tab-pane key="console" tab="Console">
          <div class="console-content">
            <div v-for="(log, index) in debugStore.consoleLogs" :key="index" class="console-item" :class="log.level">
              <span class="console-time">{{ formatTime(log.timestamp) }}</span>
              <span class="console-level">{{ log.level }}</span>
              <span class="console-message">{{ log.message }}</span>
            </div>
          </div>
        </a-tab-pane>
      </a-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useDebugStore } from '@/store/debug'
import {
  BugOutlined,
  DeleteOutlined,
  CloseOutlined,
  ExpandOutlined,
  ShrinkOutlined,
  CheckCircleOutlined
} from '@ant-design/icons-vue'

const debugStore = useDebugStore()
const isMinimized = ref(false)
const activeTab = ref('errors')

const toggleMinimize = () => {
  isMinimized.value = !isMinimized.value
}

const clearErrors = () => {
  debugStore.clearErrors()
}

const closePanel = () => {
  debugStore.disable()
}

const removeError = (index) => {
  debugStore.removeError(index)
}

const removeNetworkError = (index) => {
  debugStore.removeNetworkError(index)
}

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString()
}
</script>

<style scoped>
.debug-panel {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 600px;
  max-height: 500px;
  background: #1e1e1e;
  border: 1px solid #333;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  z-index: 9999;
  color: #d4d4d4;
  font-family: 'Consolas', 'Monaco', monospace;
  transition: all 0.3s ease;
}

.debug-panel.minimized {
  max-height: 48px;
}

.debug-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #252526;
  border-bottom: 1px solid #333;
  cursor: pointer;
  user-select: none;
  border-radius: 8px 8px 0 0;
}

.debug-title {
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.debug-actions {
  display: flex;
  gap: 12px;
}

.action-icon {
  cursor: pointer;
  font-size: 16px;
  color: #888;
  transition: color 0.2s;
}

.action-icon:hover {
  color: #d4d4d4;
}

.debug-content {
  max-height: 450px;
  overflow-y: auto;
  padding: 12px;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #888;
}

.empty-state p {
  margin-top: 16px;
  font-size: 14px;
}

.error-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.error-item {
  background: #2d2d30;
  border: 1px solid #404040;
  border-radius: 4px;
  padding: 12px;
}

.error-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.error-type {
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
}

.error-type.error {
  background: #f44336;
  color: white;
}

.error-type.warning {
  background: #ff9800;
  color: white;
}

.error-type.network {
  background: #2196f3;
  color: white;
}

.error-time {
  font-size: 11px;
  color: #888;
}

.delete-icon {
  cursor: pointer;
  color: #888;
  transition: color 0.2s;
}

.delete-icon:hover {
  color: #f44336;
}

.error-message {
  color: #f48771;
  font-size: 13px;
  margin-bottom: 8px;
  word-break: break-word;
}

.error-stack,
.error-context {
  margin-top: 8px;
}

.error-stack pre,
.error-context pre {
  background: #1e1e1e;
  padding: 8px;
  border-radius: 4px;
  font-size: 11px;
  overflow-x: auto;
  margin: 0;
  color: #ce9178;
}

.console-content {
  max-height: 350px;
  overflow-y: auto;
}

.console-item {
  padding: 6px 12px;
  border-bottom: 1px solid #333;
  display: flex;
  gap: 12px;
  font-size: 12px;
}

.console-item.error {
  background: rgba(244, 67, 54, 0.1);
}

.console-item.warn {
  background: rgba(255, 152, 0, 0.1);
}

.console-time {
  color: #888;
  min-width: 80px;
}

.console-level {
  color: #4fc3f7;
  min-width: 50px;
  font-weight: 600;
}

.console-message {
  color: #d4d4d4;
  flex: 1;
  word-break: break-word;
}

/* Scrollbar styling */
.debug-content::-webkit-scrollbar,
.console-content::-webkit-scrollbar {
  width: 8px;
}

.debug-content::-webkit-scrollbar-track,
.console-content::-webkit-scrollbar-track {
  background: #1e1e1e;
}

.debug-content::-webkit-scrollbar-thumb,
.console-content::-webkit-scrollbar-thumb {
  background: #424242;
  border-radius: 4px;
}

.debug-content::-webkit-scrollbar-thumb:hover,
.console-content::-webkit-scrollbar-thumb:hover {
  background: #4e4e4e;
}
</style>

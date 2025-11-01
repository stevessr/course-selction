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
import { theme } from 'ant-design-vue'
import {
  BugOutlined,
  DeleteOutlined,
  CloseOutlined,
  ExpandOutlined,
  ShrinkOutlined,
  CheckCircleOutlined
} from '@ant-design/icons-vue'

const { useToken } = theme
const { token } = useToken()

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
  background: v-bind('token.colorBgElevated');
  border: 1px solid v-bind('token.colorBorder');
  border-radius: v-bind('token.borderRadiusLG + "px"');
  box-shadow: v-bind('token.boxShadowSecondary');
  z-index: 9999;
  color: v-bind('token.colorText');
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
  background: v-bind('token.colorBgContainer');
  border-bottom: 1px solid v-bind('token.colorBorder');
  cursor: pointer;
  user-select: none;
  border-radius: v-bind('token.borderRadiusLG + "px"') v-bind('token.borderRadiusLG + "px"') 0 0;
}

.debug-title {
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: v-bind('token.colorTextHeading');
}

.debug-actions {
  display: flex;
  gap: 12px;
}

.action-icon {
  cursor: pointer;
  font-size: 16px;
  color: v-bind('token.colorTextSecondary');
  transition: color 0.2s;
}

.action-icon:hover {
  color: v-bind('token.colorPrimary');
}

.debug-content {
  max-height: 450px;
  overflow-y: auto;
  padding: 12px;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: v-bind('token.colorTextSecondary');
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
  background: v-bind('token.colorBgContainer');
  border: 1px solid v-bind('token.colorBorder');
  border-radius: v-bind('token.borderRadius + "px"');
  padding: 12px;
}

.error-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  gap: 12px;
}

.error-type {
  padding: 2px 8px;
  border-radius: v-bind('token.borderRadiusSM + "px"');
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
}

.error-type.error {
  background: v-bind('token.colorErrorBg');
  color: v-bind('token.colorError');
}

.error-type.warn {
  background: v-bind('token.colorWarningBg');
  color: v-bind('token.colorWarning');
}

.error-type.network {
  background: v-bind('token.colorInfoBg');
  color: v-bind('token.colorInfo');
}

.error-time {
  font-size: 11px;
  color: v-bind('token.colorTextTertiary');
}

.delete-icon {
  cursor: pointer;
  font-size: 14px;
  color: v-bind('token.colorTextSecondary');
  transition: color 0.2s;
}

.delete-icon:hover {
  color: v-bind('token.colorError');
}

.error-message {
  font-size: 13px;
  color: v-bind('token.colorText');
  word-break: break-word;
  margin-bottom: 8px;
}

.error-stack pre,
.error-context pre {
  background: v-bind('token.colorBgLayout');
  padding: 8px;
  border-radius: v-bind('token.borderRadiusSM + "px"');
  font-size: 11px;
  overflow-x: auto;
  margin: 0;
  color: v-bind('token.colorTextSecondary');
}

.console-content {
  max-height: 350px;
  overflow-y: auto;
}

.console-item {
  padding: 6px 12px;
  border-bottom: 1px solid v-bind('token.colorBorder');
  display: flex;
  gap: 12px;
  font-size: 12px;
}

.console-item.error {
  background: v-bind('token.colorErrorBg');
}

.console-item.warn {
  background: v-bind('token.colorWarningBg');
}

.console-time {
  color: v-bind('token.colorTextTertiary');
  min-width: 80px;
}

.console-level {
  color: v-bind('token.colorPrimary');
  min-width: 50px;
  font-weight: 600;
}

.console-message {
  color: v-bind('token.colorText');
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
  background: v-bind('token.colorBgLayout');
}

.debug-content::-webkit-scrollbar-thumb,
.console-content::-webkit-scrollbar-thumb {
  background: v-bind('token.colorBorder');
  border-radius: 4px;
}

.debug-content::-webkit-scrollbar-thumb:hover,
.console-content::-webkit-scrollbar-thumb:hover {
  background: v-bind('token.colorPrimaryBorder');
}
</style>

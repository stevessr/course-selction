<template>
  <div class="login-container">
    <a-card class="login-card">
      <template #title>
        <div class="login-header">
          <span>Course Selection System</span>
        </div>
      </template>
      
      <div class="role-selection">
        <h2 style="text-align: center; margin-bottom: 32px;">Select Your Role</h2>
        
        <a-space direction="vertical" :size="16" style="width: 100%">
          <a-card hoverable class="role-card" @click="goToLogin('student')">
            <div class="role-content">
              <BookOutlined class="role-icon student-icon" />
              <div class="role-info">
                <h3>Student</h3>
                <p>Browse and select courses</p>
              </div>
            </div>
          </a-card>

          <a-card hoverable class="role-card" @click="goToLogin('teacher')">
            <div class="role-content">
              <ReadOutlined class="role-icon teacher-icon" />
              <div class="role-info">
                <h3>Teacher</h3>
                <p>Manage courses and students</p>
              </div>
            </div>
          </a-card>

          <a-card hoverable class="role-card" @click="goToLogin('admin')">
            <div class="role-content">
              <CrownOutlined class="role-icon admin-icon" />
              <div class="role-info">
                <h3>Administrator</h3>
                <p>System administration</p>
              </div>
            </div>
          </a-card>
        </a-space>

        <div style="text-align: center; margin-top: 24px">
          <a-typography-text type="secondary">
            Don't have an account? <router-link to="/register">Register here</router-link>
          </a-typography-text>
        </div>
      </div>
    </a-card>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { BookOutlined, ReadOutlined, CrownOutlined } from '@ant-design/icons-vue'

const router = useRouter()

const goToLogin = (role) => {
  router.push(`/login/${role}`)
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: cornflowerblue;
}

.login-card {
  width: 100%;
  max-width: 500px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.login-header {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: bold;
}

.role-selection {
  padding: 16px 0;
}

.role-card {
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.role-card:hover {
  border-color: #1890ff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
}

.role-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.role-icon {
  font-size: 48px;
}

.student-icon {
  color: #667eea;
}

.teacher-icon {
  color: #f5576c;
}

.admin-icon {
  color: #a6c1ee;
}

.role-info h3 {
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: 600;
}

.role-info p {
  margin: 0;
  color: #666;
  font-size: 14px;
}
</style>

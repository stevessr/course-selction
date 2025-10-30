<template>
  <div class="login-container">
    <a-card class="login-card">
      <div class="login-header">
        <h1 class="title">选课系统</h1>
        <p class="subtitle">Course Selection System</p>
        <p class="description">请选择您的身份进行登录</p>
      </div>

      <a-row :gutter="[24, 24]">
        <a-col :xs="24" :sm="24" :md="8">
          <router-link to="/admin/login">
            <a-card hoverable class="role-card admin-card">
              <template #cover>
                <div class="role-icon">👨‍💼</div>
              </template>
              <a-card-meta title="管理员" description="Administrator">
                <template #description>
                  <p>系统管理和配置</p>
                </template>
              </a-card-meta>
            </a-card>
          </router-link>
        </a-col>

        <a-col :xs="24" :sm="24" :md="8">
          <router-link to="/teacher/login">
            <a-card hoverable class="role-card teacher-card">
              <template #cover>
                <div class="role-icon">👨‍🏫</div>
              </template>
              <a-card-meta title="教师" description="Teacher">
                <template #description>
                  <p>课程管理和教学</p>
                </template>
              </a-card-meta>
            </a-card>
          </router-link>
        </a-col>

        <a-col :xs="24" :sm="24" :md="8">
          <router-link to="/student/login">
            <a-card hoverable class="role-card student-card">
              <template #cover>
                <div class="role-icon">👨‍🎓</div>
              </template>
              <a-card-meta title="学生" description="Student">
                <template #description>
                  <p>选课和学习</p>
                </template>
              </a-card-meta>
            </a-card>
          </router-link>
        </a-col>
      </a-row>

      <div class="login-footer">
        <p class="footer-text">© 2025 选课系统 - Course Selection System</p>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
// This is a simple role selection page
// No logic needed, just navigation via router-link
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  padding: 48px;
  width: 100%;
  max-width: 900px;
}

.login-header {
  text-align: center;
  margin-bottom: 48px;
}

.title {
  font-size: 36px;
  font-weight: 700;
  color: #667eea;
  margin: 0 0 12px 0;
}

.subtitle {
  color: #6b7280;
  font-size: 16px;
  margin: 0 0 8px 0;
}

.description {
  color: #9ca3af;
  font-size: 14px;
  margin: 0;
}

.role-card {
  border-radius: 12px;
  text-align: center;
  transition: all 0.3s ease;
}

.role-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
}

.role-icon {
  font-size: 64px;
  padding: 24px 0;
}

.admin-card {
  border: 2px solid #667eea;
}

.teacher-card {
  border: 2px solid #f5576c;
}

.student-card {
  border: 2px solid #00f2fe;
}

.login-footer {
  text-align: center;
  padding-top: 24px;
  margin-top: 32px;
  border-top: 1px solid #e5e7eb;
}

.footer-text {
  color: #9ca3af;
  font-size: 13px;
  margin: 0;
}

@media (max-width: 768px) {
  .login-card {
    padding: 32px 24px;
  }

  .title {
    font-size: 28px;
  }

  .role-icon {
    font-size: 48px;
  }
}
</style>

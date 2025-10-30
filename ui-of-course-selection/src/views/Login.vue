<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1>选课系统</h1>
        <p class="subtitle">Course Selection System</p>
        <p class="description">请选择您的身份进行登录</p>
      </div>

      <div class="role-cards">
        <router-link to="/admin/login" class="role-card admin-card">
          <div class="role-icon">👨‍💼</div>
          <h2>管理员</h2>
          <p>Administrator</p>
          <div class="role-description">系统管理和配置</div>
        </router-link>

        <router-link to="/teacher/login" class="role-card teacher-card">
          <div class="role-icon">👨‍🏫</div>
          <h2>教师</h2>
          <p>Teacher</p>
          <div class="role-description">课程管理和教学</div>
        </router-link>

        <router-link to="/student/login" class="role-card student-card">
          <div class="role-icon">👨‍🎓</div>
          <h2>学生</h2>
          <p>Student</p>
          <div class="role-description">选课和学习</div>
        </router-link>
      </div>

      <div class="login-footer">
        <p class="footer-text">© 2025 选课系统 - Course Selection System</p>
      </div>
    </div>
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

.login-header h1 {
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

.role-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.role-card {
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  padding: 32px 24px;
  text-align: center;
  text-decoration: none;
  transition: all 0.3s ease;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.role-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
}

.admin-card {
  border-color: #667eea;
}

.admin-card:hover {
  border-color: #667eea;
  background: linear-gradient(135deg, #667eea10 0%, #764ba210 100%);
}

.teacher-card {
  border-color: #f5576c;
}

.teacher-card:hover {
  border-color: #f5576c;
  background: linear-gradient(135deg, #f093fb10 0%, #f5576c10 100%);
}

.student-card {
  border-color: #00f2fe;
}

.student-card:hover {
  border-color: #00f2fe;
  background: linear-gradient(135deg, #4facfe10 0%, #00f2fe10 100%);
}

.role-icon {
  font-size: 64px;
  margin-bottom: 8px;
}

.role-card h2 {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  color: #1f2937;
}

.role-card p {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

.role-description {
  font-size: 13px;
  color: #9ca3af;
  margin-top: 4px;
}

.admin-card h2 {
  color: #667eea;
}

.teacher-card h2 {
  color: #f5576c;
}

.student-card h2 {
  color: #00f2fe;
}

.login-footer {
  text-align: center;
  padding-top: 24px;
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

  .login-header h1 {
    font-size: 28px;
  }

  .role-cards {
    grid-template-columns: 1fr;
  }

  .role-icon {
    font-size: 48px;
  }

  .role-card h2 {
    font-size: 20px;
  }
}
</style>

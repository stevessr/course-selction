<template>
  <div class="login-container">
    <a-card class="login-card">
      <div class="login-header">
        <h1>管理员登录</h1>
        <p class="subtitle">Admin Login</p>
      </div>

      <a-form @submit.prevent="handleLogin" class="login-form">
        <a-form-item>
          <a-input
            v-model:value="username"
            placeholder="请输入管理员账号"
            :disabled="isLoading"
            size="large"
          />
        </a-form-item>

        <a-form-item>
          <a-input-password
            v-model:value="password"
            placeholder="请输入密码"
            :disabled="isLoading"
            size="large"
          />
        </a-form-item>

        <a-alert v-if="errorMessage" :message="errorMessage" type="error" show-icon />

        <a-form-item>
          <a-button type="primary" html-type="submit" :loading="isLoading" block size="large">
            登录
          </a-button>
        </a-form-item>
      </a-form>

      <div class="login-footer">
        <router-link to="/login" class="back-link">← 返回角色选择</router-link>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { loginApi } from '@/services/api';

const router = useRouter();
const authStore = useAuthStore();

const username = ref('');
const password = ref('');
const errorMessage = ref('');
const isLoading = ref(false);

// Development mode: auto-fill credentials
if (__DEV__) {
  username.value = 'admin';
  password.value = 'admin123';
}

const handleLogin = async () => {
  if (isLoading.value) return;

  errorMessage.value = '';
  isLoading.value = true;

  try {
    // Admin uses single-step login without 2FA
    const response = await loginApi.post('/login/admin', {
      admin_name: username.value,
      admin_password: password.value,
    });

    if (response.data.access_token) {
      const accessToken = response.data.access_token;
      authStore.setToken(accessToken);

      // Get user information for admin
      const userResponse = await loginApi.post(
        '/get/user',
        {},
        { headers: { access_token: accessToken } }
      );

      authStore.setUser(userResponse.data);
      router.push({ name: 'AdminDashboard' });
    } else {
      errorMessage.value = '登录失败：未收到访问令牌';
    }
  } catch (error: any) {
    console.error('Admin login error:', error);
    errorMessage.value = `登录失败：${error.response?.data?.detail || error.message}`;
  } finally {
    isLoading.value = false;
  }
};
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
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  padding: 40px;
  width: 100%;
  max-width: 420px;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: #667eea;
  margin: 0 0 8px 0;
}

.subtitle {
  color: #6b7280;
  font-size: 14px;
  margin: 0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.login-footer {
  margin-top: 24px;
  text-align: center;
}

.back-link {
  color: #667eea;
  text-decoration: none;
  font-size: 14px;
  transition: color 0.2s;
}

.back-link:hover {
  color: #764ba2;
}
</style>

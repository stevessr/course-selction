<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1>学生登录</h1>
        <p class="subtitle">Student Login</p>
      </div>

      <!-- Step 1: Username and Password -->
      <form v-if="!show2fa" @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="username">学生账号</label>
          <input
            id="username"
            v-model="username"
            type="text"
            placeholder="请输入学生账号"
            required
            :disabled="isLoading"
          />
        </div>

        <div class="form-group">
          <label for="password">密码</label>
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder="请输入密码"
            required
            :disabled="isLoading"
          />
        </div>

        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>

        <button type="submit" class="login-button" :disabled="isLoading">
          {{ isLoading ? '登录中...' : '下一步' }}
        </button>
      </form>

      <!-- Step 2: 2FA Code -->
      <form v-else @submit.prevent="handle2fa" class="login-form">
        <div class="info-message">
          <p>请输入您的两步验证码</p>
        </div>

        <div class="form-group">
          <label for="twoFactorCode">验证码</label>
          <input
            id="twoFactorCode"
            v-model="twoFactorCode"
            type="text"
            placeholder="请输入 6 位验证码"
            maxlength="6"
            pattern="[0-9]{6}"
            required
            :disabled="isLoading"
            autofocus
          />
        </div>

        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>

        <div class="button-group">
          <button type="button" @click="show2fa = false" class="back-button" :disabled="isLoading">
            返回
          </button>
          <button type="submit" class="login-button" :disabled="isLoading">
            {{ isLoading ? '验证中...' : '验证' }}
          </button>
        </div>
      </form>

      <div class="login-footer">
        <router-link to="/login" class="back-link">← 返回角色选择</router-link>
      </div>
    </div>
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
const twoFactorCode = ref('');
const errorMessage = ref('');
const isLoading = ref(false);
const show2fa = ref(false);
const refreshToken = ref('');

// Development mode: auto-fill credentials
if (__DEV__) {
  username.value = 'student1';
  password.value = 'password';
  twoFactorCode.value = '000000'; // Will be updated manually
}

// Handle initial login (step 1)
const handleLogin = async () => {
  if (isLoading.value) return;

  errorMessage.value = '';
  isLoading.value = true;

  try {
    const response = await loginApi.post('/login/v1', {
      user_name: username.value,
      user_password: password.value,
    });

    if (response.data.refresh_token) {
      refreshToken.value = response.data.refresh_token;
      show2fa.value = true;
    } else {
      errorMessage.value = '登录失败：未收到刷新令牌';
    }
  } catch (error: any) {
    console.error('Student login error:', error);
    errorMessage.value = `登录失败：${error.response?.data?.detail || error.message}`;
  } finally {
    isLoading.value = false;
  }
};

// Handle 2FA verification (step 2)
const handle2fa = async () => {
  if (isLoading.value) return;

  if (!refreshToken.value) {
    errorMessage.value = '未找到刷新令牌，请重新登录';
    return;
  }

  errorMessage.value = '';
  isLoading.value = true;

  try {
    const response = await loginApi.post(
      '/login/v2',
      { two_fa: twoFactorCode.value },
      { headers: { refresh_token: refreshToken.value } }
    );

    if (response.data.access_token) {
      const accessToken = response.data.access_token;
      authStore.setToken(accessToken);

      // Get user information
      const userResponse = await loginApi.post(
        '/get/user',
        {},
        { headers: { access_token: accessToken } }
      );

      authStore.setUser(userResponse.data);
      router.push({ name: 'StudentDashboard' });
    } else {
      errorMessage.value = '验证失败：未收到访问令牌';
    }
  } catch (error: any) {
    console.error('2FA verification error:', error);
    errorMessage.value = `验证失败：${error.response?.data?.detail || error.message}`;
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
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
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
  color: #00f2fe;
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

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.form-group input {
  padding: 12px 16px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: #00f2fe;
  box-shadow: 0 0 0 3px rgba(0, 242, 254, 0.1);
}

.form-group input:disabled {
  background-color: #f3f4f6;
  cursor: not-allowed;
}

.info-message {
  padding: 12px;
  background-color: #dbeafe;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  color: #1e40af;
  font-size: 14px;
}

.info-message p {
  margin: 0;
}

.error-message {
  padding: 12px;
  background-color: #fee2e2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  font-size: 14px;
}

.login-button {
  padding: 12px 24px;
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.login-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 242, 254, 0.4);
}

.login-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.button-group {
  display: flex;
  gap: 12px;
}

.back-button {
  flex: 1;
  padding: 12px 24px;
  background: #f3f4f6;
  color: #374151;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.back-button:hover:not(:disabled) {
  background: #e5e7eb;
}

.back-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.login-footer {
  margin-top: 24px;
  text-align: center;
}

.back-link {
  color: #00f2fe;
  text-decoration: none;
  font-size: 14px;
  transition: color 0.2s;
}

.back-link:hover {
  color: #4facfe;
}
</style>


<template>
  <div class="login-container">
    <a-card class="login-card">
      <div class="login-header">
        <h1>教师登录</h1>
        <p class="subtitle">Teacher Login</p>
      </div>

      <!-- Step 1: Username and Password -->
      <a-form v-if="!show2fa" @submit.prevent="handleLogin" class="login-form">
        <a-form-item>
          <a-input
            v-model:value="username"
            placeholder="请输入教师账号"
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
            下一步
          </a-button>
        </a-form-item>
      </a-form>

      <!-- Step 2: 2FA Code -->
      <a-form v-else @submit.prevent="handle2fa" class="login-form">
        <div class="info-message">
          <p>请输入您的两步验证码</p>
        </div>

        <a-form-item>
          <a-input
            v-model:value="twoFactorCode"
            placeholder="请输入 6 位验证码"
            :maxlength="6"
            :disabled="isLoading"
            size="large"
            autofocus
          />
        </a-form-item>

        <a-alert v-if="errorMessage" :message="errorMessage" type="error" show-icon />

        <a-form-item>
          <a-row :gutter="16">
            <a-col :span="12">
              <a-button @click="show2fa = false" :disabled="isLoading" block size="large">
                返回
              </a-button>
            </a-col>
            <a-col :span="12">
              <a-button type="primary" html-type="submit" :loading="isLoading" block size="large">
                验证
              </a-button>
            </a-col>
          </a-row>
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
const twoFactorCode = ref('');
const errorMessage = ref('');
const isLoading = ref(false);
const show2fa = ref(false);
const refreshToken = ref('');

// Development mode: auto-fill credentials
if (__DEV__) {
  username.value = 'teacher1';
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
    console.error('Teacher login error:', error);
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
      router.push({ name: 'TeacherDashboard' });
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
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
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
  color: #f5576c;
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

.info-message {
  padding: 12px;
  background-color: #dbeafe;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  color: #1e40af;
  font-size: 14px;
  text-align: center;
}

.info-message p {
  margin: 0;
}

.login-footer {
  margin-top: 24px;
  text-align: center;
}

.back-link {
  color: #f5576c;
  text-decoration: none;
  font-size: 14px;
  transition: color 0.2s;
}

.back-link:hover {
  color: #f093fb;
}
</style>

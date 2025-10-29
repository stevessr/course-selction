<template>
  <div class="login-container">
    <div class="login-box">
      <h1>Login</h1>
      <form @submit.prevent="handleLogin" v-if="!show2fa">
        <div class="input-group">
          <label for="username">Username</label>
          <input type="text" id="username" v-model="username" required />
        </div>
        <div class="input-group">
          <label for="password">Password</label>
          <input type="password" id="password" v-model="password" required />
        </div>
        <button type="submit" class="login-button">Login</button>
      </form>

      <form @submit.prevent="handle2fa" v-if="show2fa">
        <div class="input-group">
          <label for="2fa">2FA Code</label>
          <input type="text" id="2fa" v-model="twoFactorCode" required />
        </div>
        <button type="submit" class="login-button">Verify</button>
      </form>

      <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { loginApi } from '@/services/api';
import { useAuthStore } from '@/stores/auth';

const username = ref('');
const password = ref('');
const twoFactorCode = ref('');
const errorMessage = ref('');
const show2fa = ref(false);
const refreshToken = ref<string | null>(null);

const router = useRouter();
const authStore = useAuthStore();

const handleLogin = async () => {
  try {
    const response = await loginApi.post('/login/v1', {
      user_name: username.value,
      user_password: password.value,
    });

    if (response.data.refresh_token) {
      refreshToken.value = response.data.refresh_token;
      show2fa.value = true;
      errorMessage.value = '';
    } else {
      errorMessage.value = 'Login failed: No refresh token received.';
    }
  } catch (error: any) {
    errorMessage.value = `Login failed: ${error.response?.data?.detail || error.message}`;
  }
};

const handle2fa = async () => {
  if (!refreshToken.value) {
    errorMessage.value = 'No refresh token found. Please try logging in again.';
    return;
  }

  try {
    const response = await loginApi.post('/login/v2', 
      { fa_code: twoFactorCode.value }, 
      { headers: { Authorization: `Bearer ${refreshToken.value}` } 
    });

    if (response.data.access_token) {
      const accessToken = response.data.access_token;
      authStore.setToken(accessToken);

      const userResponse = await loginApi.post('/get/user', { access_token: accessToken });
      authStore.setUser(userResponse.data);

      switch (userResponse.data.user_type) {
        case 'student':
          router.push({ name: 'StudentDashboard' });
          break;
        case 'teacher':
          router.push({ name: 'TeacherDashboard' });
          break;
        case 'admin':
          router.push({ name: 'AdminDashboard' });
          break;
        default:
          router.push('/');
      }
    } else {
      errorMessage.value = '2FA verification failed: No access token received.';
    }
  } catch (error: any) {
    errorMessage.value = `2FA verification failed: ${error.response?.data?.detail || error.message}`;
  }
};
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f0f2f5;
}

.login-box {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
  text-align: center;
}

h1 {
  margin-bottom: 1.5rem;
}

.input-group {
  margin-bottom: 1rem;
  text-align: left;
}

.input-group label {
  display: block;
  margin-bottom: 0.5rem;
}

.input-group input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.login-button {
  width: 100%;
  padding: 0.75rem;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}

.login-button:hover {
  background-color: #0056b3;
}

.error-message {
  color: red;
  margin-top: 1rem;
}
</style>

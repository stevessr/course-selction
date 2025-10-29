<template>
  <div class="login-container">
    <div class="login-box">
      <h1>{{ show2fa ? '2FA Verification' : 'Login' }}</h1>

      <!-- Role selection for development mode -->
      <div class="role-selection" v-if="!show2fa && isDev">
        <label class="role-label">Login as:</label>
        <div class="role-options">
          <label class="role-option">
            <input type="radio" id="admin" value="admin" v-model="selectedRole" />
            <span>Admin</span>
          </label>
          <label class="role-option">
            <input type="radio" id="teacher" value="teacher" v-model="selectedRole" />
            <span>Teacher</span>
          </label>
          <label class="role-option">
            <input type="radio" id="student" value="student" v-model="selectedRole" />
            <span>Student</span>
          </label>
        </div>
      </div>

      <!-- Login form -->
      <form @submit.prevent="handleLogin" v-if="!show2fa">
        <div class="input-group">
          <label for="username">Username</label>
          <input
            type="text"
            id="username"
            v-model="username"
            :disabled="isLoading"
            required
            autocomplete="username"
          />
        </div>
        <div class="input-group">
          <label for="password">Password</label>
          <input
            type="password"
            id="password"
            v-model="password"
            :disabled="isLoading"
            required
            autocomplete="current-password"
          />
        </div>
        <button type="submit" class="login-button" :disabled="isLoading">
          {{ isLoading ? 'Logging in...' : 'Login' }}
        </button>
      </form>

      <!-- 2FA form -->
      <form @submit.prevent="handle2fa" v-if="show2fa">
        <div class="input-group">
          <label for="2fa">2FA Code</label>
          <input
            type="text"
            id="2fa"
            v-model="twoFactorCode"
            :disabled="isLoading"
            required
            autocomplete="one-time-code"
            placeholder="Enter 6-digit code"
          />
        </div>
        <button type="submit" class="login-button" :disabled="isLoading">
          {{ isLoading ? 'Verifying...' : 'Verify' }}
        </button>
        <button type="button" class="back-button" @click="goBackToLogin" :disabled="isLoading">
          Back to Login
        </button>
      </form>

      <!-- Error message -->
      <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { loginApi } from '@/services/api';
import { useAuthStore } from '@/stores/auth';

// Type definitions
type RoleType = 'admin' | 'teacher' | 'student';

interface Credentials {
  username: string;
  password: string;
  twoFactorCode: string;
}

// Constants
const isDev = __DEV__;

// Reactive state
const username = ref('');
const password = ref('');
const twoFactorCode = ref('');
const errorMessage = ref('');
const show2fa = ref(false);
const refreshToken = ref<string | null>(null);
const selectedRole = ref<RoleType>('admin'); // Default selected role for dev
const isLoading = ref(false);

const router = useRouter();
const authStore = useAuthStore();

// Default credentials for development mode
const defaultCredentials: Record<RoleType, Credentials> = {
  admin: { username: 'admin', password: 'password', twoFactorCode: '123456' },
  teacher: { username: 'teacher', password: 'password', twoFactorCode: '123456' },
  student: { username: 'student', password: 'password', twoFactorCode: '123456' },
};

// Fill credentials based on selected role (dev mode only)
const fillCredentials = (role: RoleType) => {
  if (__DEV__ && defaultCredentials[role]) {
    username.value = defaultCredentials[role].username;
    password.value = defaultCredentials[role].password;
    twoFactorCode.value = defaultCredentials[role].twoFactorCode;
  }
};

// Initialize credentials on mount
onMounted(() => {
  fillCredentials(selectedRole.value);
});

// Watch for role changes and update credentials
watch(selectedRole, (newRole) => {
  fillCredentials(newRole);
  errorMessage.value = ''; // Clear error when switching roles
});

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
      errorMessage.value = 'Login failed: No refresh token received.';
    }
  } catch (error: any) {
    console.error('Login error:', error);
    errorMessage.value = `Login failed: ${error.response?.data?.detail || error.message}`;
  } finally {
    isLoading.value = false;
  }
};

// Handle 2FA verification (step 2)
const handle2fa = async () => {
  if (isLoading.value) return;

  if (!refreshToken.value) {
    errorMessage.value = 'No refresh token found. Please try logging in again.';
    return;
  }

  errorMessage.value = '';
  isLoading.value = true;

  try {
    // Send 2FA code with refresh token in header
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
        '/login/get/user',
        {},
        { headers: { access_token: accessToken } }
      );

      authStore.setUser(userResponse.data);

      // Redirect based on user type
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
    console.error('2FA verification error:', error);
    errorMessage.value = `2FA verification failed: ${error.response?.data?.detail || error.message}`;
  } finally {
    isLoading.value = false;
  }
};

// Go back to login form from 2FA
const goBackToLogin = () => {
  show2fa.value = false;
  refreshToken.value = null;
  errorMessage.value = '';
  twoFactorCode.value = defaultCredentials[selectedRole.value]?.twoFactorCode || '';
};
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 1rem;
}

.login-box {
  background: white;
  padding: 2.5rem;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  width: 100%;
  max-width: 420px;
  text-align: center;
}

h1 {
  margin-bottom: 1.5rem;
  color: #333;
  font-size: 1.75rem;
  font-weight: 600;
}

/* Role selection styles */
.role-selection {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.role-label {
  display: block;
  margin-bottom: 0.75rem;
  font-weight: 600;
  color: #555;
  font-size: 0.95rem;
}

.role-options {
  display: flex;
  justify-content: space-around;
  gap: 0.5rem;
}

.role-option {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.role-option:hover {
  background-color: #e9ecef;
}

.role-option input[type="radio"] {
  cursor: pointer;
  margin: 0;
}

.role-option span {
  font-size: 0.9rem;
  color: #555;
}

/* Form styles */
.input-group {
  margin-bottom: 1.25rem;
  text-align: left;
}

.input-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #555;
  font-size: 0.95rem;
}

.input-group input {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color 0.3s, box-shadow 0.3s;
  box-sizing: border-box;
}

.input-group input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.input-group input:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
  opacity: 0.6;
}

/* Button styles */
.login-button {
  width: 100%;
  padding: 0.875rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
  transition: transform 0.2s, box-shadow 0.2s;
  margin-bottom: 0.75rem;
}

.login-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.login-button:active:not(:disabled) {
  transform: translateY(0);
}

.login-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.back-button {
  width: 100%;
  padding: 0.875rem;
  background-color: #6c757d;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
  transition: background-color 0.2s, transform 0.2s;
}

.back-button:hover:not(:disabled) {
  background-color: #5a6268;
  transform: translateY(-2px);
}

.back-button:active:not(:disabled) {
  transform: translateY(0);
}

.back-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Error message */
.error-message {
  color: #dc3545;
  margin-top: 1rem;
  padding: 0.75rem;
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 6px;
  font-size: 0.9rem;
  text-align: left;
}

/* Responsive design */
@media (max-width: 480px) {
  .login-box {
    padding: 1.5rem;
  }

  h1 {
    font-size: 1.5rem;
  }

  .role-options {
    flex-direction: column;
    gap: 0.5rem;
  }

  .role-option {
    justify-content: center;
  }
}
</style>

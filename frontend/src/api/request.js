import axios from 'axios'
import { useDebugStore } from '@/store/debug'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Store request metadata for debugging
    config.metadata = { startTime: new Date() }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    // Track network errors in debug panel
    const debugStore = useDebugStore()
    
    if (debugStore.isEnabled) {
      debugStore.addNetworkError({
        method: error.config?.method?.toUpperCase() || 'UNKNOWN',
        url: error.config?.url || 'Unknown URL',
        status: error.response?.status || 'Network Error',
        response: error.response?.data || { message: error.message }
      })
    }
    
    // Check if the error is due to invalid token
    const status = error.response?.status;
    const message = error.response?.data?.detail || error.message || 'An error occurred';
    
    // If the error is due to invalid token (status 401) or the message contains "Invalid token"
    if (status === 401 || (typeof message === 'string' && message.includes('Invalid token'))) {
      // Automatically logout the user from auth store
      import('@/store/auth').then(module => {
        const authStore = module.useAuthStore();
        authStore.logout();
      });
    }
    
    return Promise.reject(new Error(message))
  }
)

export default api

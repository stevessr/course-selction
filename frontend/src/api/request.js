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
    
    // Extract error message safely
    let message = 'An error occurred';
    if (error.response?.data) {
      // FastAPI returns errors in 'detail' field
      if (typeof error.response.data.detail === 'string') {
        message = error.response.data.detail;
      } else if (typeof error.response.data.message === 'string') {
        message = error.response.data.message;
      } else if (typeof error.response.data === 'string') {
        message = error.response.data;
      }
    } else if (error.message) {
      message = error.message;
    }
    
    const status = error.response?.status;
    
    // If the error is due to invalid token (status 401) or the message contains "Invalid token"
    if (status === 401 || (typeof message === 'string' && message.includes('Invalid token'))) {
      // Automatically logout the user from auth store
      import('@/store/auth').then(module => {
        const authStore = module.useAuthStore();
        authStore.logout();
      });
    }
    
    // Create a proper error object with the message
    const errorObj = new Error(message);
    errorObj.response = error.response;
    errorObj.status = status;
    
    return Promise.reject(errorObj)
  }
)

export default api

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
    
    const message = error.response?.data?.detail || error.message || 'An error occurred'
    return Promise.reject(new Error(message))
  }
)

export default api

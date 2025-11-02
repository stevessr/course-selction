import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useDebugStore = defineStore('debug', () => {
  const isEnabled = ref(false)
  const errors = ref([])
  const networkErrors = ref([])
  const consoleLogs = ref([])

  // Enable/disable debug panel
  const enable = () => {
    isEnabled.value = true
    
    // Intercept console methods
    if (!window._originalConsole) {
      window._originalConsole = {
        log: console.log,
        warn: console.warn,
        error: console.error
      }
      
      console.log = (...args) => {
        addConsoleLog('log', args.map(arg => String(arg)).join(' '))
        window._originalConsole.log(...args)
      }
      
      console.warn = (...args) => {
        addConsoleLog('warn', args.map(arg => String(arg)).join(' '))
        window._originalConsole.warn(...args)
      }
      
      console.error = (...args) => {
        addConsoleLog('error', args.map(arg => String(arg)).join(' '))
        window._originalConsole.error(...args)
      }
    }
    
    // Intercept global errors
    if (!window._errorHandler) {
      window._errorHandler = (event) => {
        addError({
          type: 'error',
          message: event.message,
          stack: event.error?.stack,
          context: {
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno
          }
        })
      }
      window.addEventListener('error', window._errorHandler)
    }
    
    // Intercept unhandled promise rejections
    if (!window._rejectionHandler) {
      window._rejectionHandler = (event) => {
        addError({
          type: 'error',
          message: event.reason?.message || String(event.reason),
          stack: event.reason?.stack,
          context: {
            promise: 'Unhandled Promise Rejection'
          }
        })
      }
      window.addEventListener('unhandledrejection', window._rejectionHandler)
    }
  }

  const disable = () => {
    isEnabled.value = false
  }

  const addError = (error) => {
    errors.value.unshift({
      ...error,
      timestamp: Date.now()
    })
    
    // Keep only last 50 errors
    if (errors.value.length > 50) {
      errors.value = errors.value.slice(0, 50)
    }
  }

  const addNetworkError = (error) => {
    networkErrors.value.unshift({
      ...error,
      timestamp: Date.now()
    })
    
    // Keep only last 50 network errors
    if (networkErrors.value.length > 50) {
      networkErrors.value = networkErrors.value.slice(0, 50)
    }
  }

  const addConsoleLog = (level, message) => {
    consoleLogs.value.unshift({
      level,
      message,
      timestamp: Date.now()
    })
    
    // Keep only last 100 logs
    if (consoleLogs.value.length > 100) {
      consoleLogs.value = consoleLogs.value.slice(0, 100)
    }
  }

  const clearErrors = () => {
    errors.value = []
    networkErrors.value = []
    consoleLogs.value = []
  }

  const removeError = (index) => {
    errors.value.splice(index, 1)
  }

  const removeNetworkError = (index) => {
    networkErrors.value.splice(index, 1)
  }

  // Check localStorage for debug mode persistence
  const checkDebugMode = () => {
    const debugMode = localStorage.getItem('debug_mode')
    if (debugMode === 'enabled') {
      enable()
    }
  }

  // Toggle debug mode
  const toggle = () => {
    if (isEnabled.value) {
      disable()
      localStorage.removeItem('debug_mode')
    } else {
      enable()
      localStorage.setItem('debug_mode', 'enabled')
    }
  }

  return {
    isEnabled,
    errors,
    networkErrors,
    consoleLogs,
    enable,
    disable,
    toggle,
    addError,
    addNetworkError,
    clearErrors,
    removeError,
    removeNetworkError,
    checkDebugMode
  }
})

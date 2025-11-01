import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import authApi from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref(localStorage.getItem('accessToken') || null)
  const refreshToken = ref(localStorage.getItem('refreshToken') || null)
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const totpSecret = ref(null)
  const totpUri = ref(null)

  const isAuthenticated = computed(() => !!accessToken.value)
  const userType = computed(() => user.value?.user_type || null)
  const username = computed(() => user.value?.username || null)

  function setTokens(access, refresh) {
    accessToken.value = access
    refreshToken.value = refresh
    
    if (access) localStorage.setItem('accessToken', access)
    else localStorage.removeItem('accessToken')
    
    if (refresh) localStorage.setItem('refreshToken', refresh)
    else localStorage.removeItem('refreshToken')
  }

  function setUser(userData) {
    user.value = userData
    if (userData) {
      localStorage.setItem('user', JSON.stringify(userData))
    } else {
      localStorage.removeItem('user')
    }
  }

  function setTotpInfo(secret, uri) {
    totpSecret.value = secret
    totpUri.value = uri
  }

  async function login(username, password) {
    try {
      const response = await authApi.loginV1(username, password)
      setTokens(null, response.refresh_token)
      return { success: true, needsTwoFactor: true }
    } catch (error) {
      // Handle specific error cases
      let errorMessage = error.message || 'Login failed';
      if (errorMessage === 'Account is inactive') {
        errorMessage = 'Your account is currently inactive. Please contact the system administrator.';
      }
      return { success: false, error: errorMessage }
    }
  }

  async function adminLogin(username, password) {
    try {
      const response = await authApi.adminLogin(username, password)
      
      // Admin login might return different token format than regular login
      // Check if response has at least access_token
      if (!response.access_token) {
        return { success: false, error: 'Invalid response from server - missing access token' }
      }
      
      // Use the refresh_token if available, otherwise use the access_token as both
      // This might be a temporary solution depending on backend implementation
      const accessToken = response.access_token
      const refreshToken = response.refresh_token || response.access_token // fallback if no refresh token
      
      setTokens(accessToken, refreshToken)
      
      // Fetch user info
      const userInfo = await authApi.getUserInfo(accessToken)
      setUser(userInfo)
      
      return { success: true }
    } catch (error) {
      console.error('Admin login error:', error)
      let errorMessage = 'Admin login failed'
      if (error.response) {
        // Server responded with error status
        if (error.response.status === 401) {
          errorMessage = 'Invalid admin credentials'
        } else if (error.response.status === 403) {
          errorMessage = 'Access denied - admin privileges required'
        } else if (error.response.data && error.response.data.detail) {
          errorMessage = error.response.data.detail
        } else {
          errorMessage = `Server error: ${error.response.status}`
        }
      } else if (error.request) {
        // Request was made but no response received
        errorMessage = 'Network error - unable to reach server'
      } else {
        // Something else happened
        errorMessage = error.message || 'An unexpected error occurred'
      }
      return { success: false, error: errorMessage }
    }
  }

  async function verify2FA(totpCode) {
    try {
      const response = await authApi.loginV2(refreshToken.value, totpCode)
      setTokens(response.access_token, refreshToken.value)
      
      // Fetch user info
      const userInfo = await authApi.getUserInfo(response.access_token)
      setUser(userInfo)
      
      return { success: true }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  async function register(username, password, userType, registrationCode) {
    try {
      const response = await authApi.registerV1(username, password, userType, registrationCode)
      setTokens(null, response.refresh_token)
      setTotpInfo(response.totp_secret, response.totp_uri)
      return { 
        success: true, 
        needsTwoFactor: true,
        totpSecret: response.totp_secret,
        totpUri: response.totp_uri
      }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  async function completeRegistration(totpCode) {
    try {
      const response = await authApi.registerV2(refreshToken.value, totpCode)
      setTokens(response.access_token, refreshToken.value)
      
      // Fetch user info
      const userInfo = await authApi.getUserInfo(response.access_token)
      setUser(userInfo)
      
      return { success: true }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  async function logout() {
    try {
      if (refreshToken.value) {
        await authApi.logout(refreshToken.value)
      }
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      setTokens(null, null)
      setUser(null)
      setTotpInfo(null, null)
    }
  }

  async function refreshAccessToken(totpCode) {
    try {
      const response = await authApi.refreshToken(refreshToken.value, totpCode)
      setTokens(response.access_token, refreshToken.value)
      return { success: true }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  async function check2FAStatus() {
    try {
      const response = await authApi.check2FAStatus(refreshToken.value)
      return { success: true, ...response }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  async function loginNo2FA() {
    try {
      const response = await authApi.loginNo2FA(refreshToken.value)
      setTokens(response.access_token, refreshToken.value)
      
      // Fetch user info
      const userInfo = await authApi.getUserInfo(response.access_token)
      setUser(userInfo)
      
      return { success: true }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  async function reset2FAWithCode(resetCode, newTotpCode) {
    try {
      await authApi.reset2FA(resetCode, newTotpCode)
      return { success: true }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  function restoreSession() {
    // Session is automatically restored from localStorage in the initial refs
    // This function can be used for additional validation if needed
  }

  return {
    accessToken,
    refreshToken,
    user,
    totpSecret,
    totpUri,
    isAuthenticated,
    userType,
    username,
    login,
    adminLogin,
    verify2FA,
    register,
    completeRegistration,
    logout,
    refreshAccessToken,
    check2FAStatus,
    loginNo2FA,
    reset2FAWithCode,
    restoreSession,
    // expose internal helpers for UI code
    setTokens,
    setUser,
    setTotpInfo,
  }
})

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
      return { success: false, error: error.message }
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
    verify2FA,
    register,
    completeRegistration,
    logout,
    refreshAccessToken,
    restoreSession,
  }
})

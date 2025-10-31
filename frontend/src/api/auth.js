import api from './request'

const authApi = {
  // Student/Teacher login
  loginV1(username, password) {
    return api.post('/auth/login/v1', { username, password })
  },

  loginV2(refreshToken, totpCode) {
    return api.post('/auth/login/v2', 
      { totp_code: totpCode },
      { headers: { Authorization: `Bearer ${refreshToken}` } }
    )
  },

  // Registration
  registerV1(username, password, userType, registrationCode) {
    return api.post('/auth/register/v1', {
      username,
      password,
      user_type: userType,
      registration_code: registrationCode || undefined,
    })
  },

  registerV2(refreshToken, totpCode) {
    return api.post('/auth/register/v2',
      { totp_code: totpCode },
      { headers: { Authorization: `Bearer ${refreshToken}` } }
    )
  },

  // Logout
  logout(token) {
    return api.post('/auth/logout',
      {},
      { headers: { Authorization: `Bearer ${token}` } }
    )
  },

  // Refresh token
  refreshToken(refreshToken, totpCode) {
    return api.post('/auth/refresh',
      { totp_code: totpCode },
      { headers: { Authorization: `Bearer ${refreshToken}` } }
    )
  },

  // Get user info
  getUserInfo(accessToken) {
    return api.get('/auth/get/user',
      { headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Admin login
  adminLogin(username, password) {
    return api.post('/auth/login/admin', { username, password })
  },

  // Generate registration code
  generateRegistrationCode(accessToken, userType, expiresDays = 7) {
    return api.post('/auth/generate/registration-code',
      { user_type: userType, expires_days: expiresDays },
      { headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Generate reset code
  generateResetCode(accessToken, username, expiresDays = 7) {
    return api.post('/auth/generate/reset-code',
      { username, expires_days: expiresDays },
      { headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Reset 2FA
  reset2FA(resetCode, newTotpCode) {
    return api.post('/auth/reset/2fa', {
      reset_code: resetCode,
      new_totp_code: newTotpCode,
    })
  },
}

export default authApi

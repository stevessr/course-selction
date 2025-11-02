import api from './request'

const adminApi = {
  // User Management
  
  // List all users
  listUsers(accessToken, userType = null, page = 1, pageSize = 20, search = '') {
    return api.get('/auth/admin/users', {
      params: { user_type: userType, page, page_size: pageSize, search },
      headers: { Authorization: `Bearer ${accessToken}` }
    })
  },

  // Add new user (student/teacher/admin)
  addUser(accessToken, userData) {
    return api.post('/auth/admin/user/add', userData, {
      headers: { Authorization: `Bearer ${accessToken}` }
    })
  },

  // Delete user
  deleteUser(accessToken, userId, userType) {
    return api.post('/auth/admin/user/delete', 
      { user_id: userId, user_type: userType },
      { headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Reset user 2FA
  resetUser2FA(accessToken, username) {
    return api.post('/auth/admin/user/reset-2fa',
      { username },
      { headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Toggle user status (activate/deactivate)
  toggleUserStatus(accessToken, userId, isActive) {
    return api.post('/auth/admin/user/toggle-status',
      { user_id: userId, is_active: isActive },
      { headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Batch import users from CSV
  importUsers(accessToken, formData) {
    return api.post('/auth/admin/users/import', formData, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // Get user details
  getUserDetails(accessToken, userId, userType) {
    return api.get(`/auth/admin/user/${userId}`, {
      params: { user_type: userType },
      headers: { Authorization: `Bearer ${accessToken}` }
    })
  },

  // Update student tags
  updateStudentTags(accessToken, studentId, studentTags) {
    return api.post('/auth/admin/student/update-tags',
      { student_id: studentId, student_tags: studentTags },
      { headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Course Management (Admin access)
  
  // Import courses from CSV
  importCourses(accessToken, formData) {
    return api.post('/teacher/courses/import', formData, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // Get schedule configuration
  getScheduleConfig(accessToken) {
    return api.get('/data/courses/schedule-config', {
      headers: { Authorization: `Bearer ${accessToken}` }
    })
  },

  // Statistics

  // Get system statistics
  getSystemStats(accessToken) {
    return api.get('/auth/admin/stats', {
      headers: { Authorization: `Bearer ${accessToken}` }
    })
  },
}

export default adminApi

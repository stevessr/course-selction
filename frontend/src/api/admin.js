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

  // Reset user password
  resetUserPassword(accessToken, username, userType, newPassword = null) {
    const data = { username, user_type: userType }
    if (newPassword) {
      data.new_password = newPassword
    }
    return api.post('/auth/admin/user/reset-password',
      data,
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
    // Send student_tags as query parameters for the backend to properly parse as List[str]
    const params = new URLSearchParams()
    params.append('student_id', studentId)
    // Add each tag as a separate query parameter
    if (Array.isArray(studentTags)) {
      studentTags.forEach(tag => {
        params.append('student_tags', tag)
      })
    }
    
    return api.post('/auth/admin/student/update-tags',
      { student_id: studentId, student_tags: studentTags },
      { headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Get available tags for autocomplete
  getAvailableTags(accessToken, tagType = null) {
    return api.get('/data/tags/available', {
      params: tagType ? { tag_type: tagType } : {},
      headers: { Authorization: `Bearer ${accessToken}` }
    })
  },

  // Course Management (Admin access)
  
  // List all courses
  listCourses(accessToken, page = 1, pageSize = 20, search = '', courseType = null) {
    return api.get('/auth/admin/courses', {
      params: { page, page_size: pageSize, search, course_type: courseType },
      headers: { Authorization: `Bearer ${accessToken}` }
    })
  },

  // Update course
  updateCourse(accessToken, courseData) {
    return api.post('/auth/admin/course/update', courseData, {
      headers: { Authorization: `Bearer ${accessToken}` }
    })
  },

  // Delete course
  deleteCourse(accessToken, courseId) {
    return api.post('/auth/admin/course/delete', 
      { course_id: courseId },
      { headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Bulk import courses
  bulkImportCourses(accessToken, coursesData) {
    return api.post('/auth/admin/courses/bulk-import', coursesData, {
      headers: { Authorization: `Bearer ${accessToken}` }
    })
  },

  // Batch assign teacher to courses
  batchAssignTeacher(accessToken, courseIds, teacherId) {
    return api.post('/auth/admin/courses/batch-assign-teacher', 
      { course_ids: courseIds, teacher_id: teacherId },
      { headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Export users
  exportUsers(accessToken, userType = null, userIds = []) {
    return api.post('/auth/admin/users/export',
      { user_type: userType, user_ids: userIds },
      { headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },
  
  // Import courses from CSV (old endpoint - keep for compatibility)
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

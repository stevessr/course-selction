import api from './request'

const studentApi = {
  // Get available courses
  getAvailableCourses(accessToken, courseType = null, page = 1, pageSize = 20) {
    return api.post('/student/student/courses/available',
      { course_type: courseType, page, page_size: pageSize },
      { headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Get selected courses
  getSelectedCourses(accessToken) {
    return api.get('/student/student/courses/selected',
      { headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Select course
  selectCourse(accessToken, courseId) {
    return api.post('/student/student/course/select',
      { course_id: courseId },
      { headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Deselect course
  deselectCourse(accessToken, courseId) {
    return api.post('/student/student/course/deselect',
      { course_id: courseId },
      { headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Get course detail
  getCourseDetail(accessToken, courseId) {
    return api.post('/student/student/course/detail',
      { course_id: courseId },
      { headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Get schedule
  getSchedule(accessToken) {
    return api.get('/student/student/schedule',
      { headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Get stats
  getStats(accessToken) {
    return api.get('/student/student/stats',
      { headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Get queue status
  getQueueStatus(accessToken, taskId) {
    return api.get(`/student/student/queue/status?task_id=${taskId}`,
      { headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Check course conflicts
  checkCourseConflicts(accessToken, courseId) {
    return api.post('/student/student/course/check',
      { course_id: courseId },
      { headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },
}

export default studentApi

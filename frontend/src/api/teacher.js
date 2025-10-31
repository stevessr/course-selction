import api from './request'

const teacherApi = {
  // Get teacher's courses
  getCourses(accessToken) {
    return api.get('/teacher/teacher/courses',
      { headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Get course detail
  getCourseDetail(accessToken, courseId) {
    return api.post('/teacher/teacher/course/detail',
      { course_id: courseId },
      { headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Create course
  createCourse(accessToken, courseData) {
    return api.post('/teacher/teacher/course/create',
      courseData,
      { headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Update course
  updateCourse(accessToken, courseId, courseData) {
    return api.put('/teacher/teacher/course/update',
      { course_id: courseId, ...courseData },
      { headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Delete course
  deleteCourse(accessToken, courseId) {
    return api.delete('/teacher/teacher/course/delete',
      { 
        data: { course_id: courseId },
        headers: { Authorization: `Bearer ${accessToken}` } 
      }
    )
  },

  // Remove student from course
  removeStudent(accessToken, courseId, studentId) {
    return api.post('/teacher/teacher/student/remove',
      { course_id: courseId, student_id: studentId },
      { headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Get stats
  getStats(accessToken) {
    return api.get('/teacher/teacher/stats',
      { headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },
}

export default teacherApi

import api from './request'

const teacherApi = {
  // Get teacher's courses
  getCourses(accessToken) {
    return api.get('/teacher/courses',
      { headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Get course detail
  getCourseDetail(accessToken, courseId) {
    // Backend expects course_id as query param on a POST endpoint
    return api.post('/teacher/course/detail',
      null,
      { params: { course_id: courseId }, headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Create course
  createCourse(accessToken, courseData) {
    return api.post('/teacher/course/create',
      courseData,
      { headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Update course
  updateCourse(accessToken, courseId, courseData) {
    // Backend expects course_id as query param and body as CourseUpdate
    return api.put('/teacher/course/update',
      courseData,
      { params: { course_id: courseId }, headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Delete course
  deleteCourse(accessToken, courseId) {
    return api.delete('/teacher/course/delete',
      { params: { course_id: courseId }, headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Bulk import courses
  bulkImportCourses(accessToken, coursesData) {
    return api.post('/teacher/courses/bulk-import',
      coursesData,
      { headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Remove student from course
  removeStudent(accessToken, courseId, studentId) {
    return api.post('/teacher/student/remove',
      null,
      { params: { course_id: courseId, student_id: studentId }, headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Get students enrolled in a course
  getCourseStudents(accessToken, courseId) {
    return api.get('/teacher/course/students',
      { params: { course_id: courseId }, headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Get all students (for adding to courses)
  getStudents(accessToken) {
    return api.get('/teacher/students',
      { headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Add students to a course
  addStudentsToCourse(accessToken, courseId, studentIds) {
    return api.post('/teacher/course/add-students',
      { course_id: courseId, student_ids: studentIds },
      { headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Bulk add students to course by usernames
  bulkAddStudentsToCourse(accessToken, courseId, usernames) {
    return api.post('/teacher/course/bulk-add-students',
      { course_id: courseId, usernames },
      { headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },

  // Get stats
  getStats(accessToken) {
    return api.get('/teacher/stats',
      { headers: { Authorization: `Bearer ${accessToken}` } }
    )
  },
}

export default teacherApi

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const routes = [
  {
    path: '/',
    redirect: '/login',
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/login/student',
    name: 'LoginStudent',
    component: () => import('@/views/LoginStudent.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/login/teacher',
    name: 'LoginTeacher',
    component: () => import('@/views/LoginTeacher.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/login/admin',
    name: 'LoginAdmin',
    component: () => import('@/views/LoginAdmin.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/student/setup-2fa',
    name: 'StudentSetup2FA',
    component: () => import('@/views/student/Setup2FA.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/student',
    name: 'Student',
    component: () => import('@/views/student/Layout.vue'),
    meta: { requiresAuth: true, role: 'student' },
    children: [
      {
        path: 'courses',
        name: 'StudentCourses',
        component: () => import('@/views/student/Courses.vue'),
      },
      {
        path: 'selected',
        name: 'StudentSelected',
        component: () => import('@/views/student/SelectedCourses.vue'),
      },
      {
        path: 'schedule',
        name: 'StudentSchedule',
        component: () => import('@/views/student/Schedule.vue'),
      },
    ],
  },
  {
    path: '/teacher',
    name: 'Teacher',
    component: () => import('@/views/teacher/Layout.vue'),
    meta: { requiresAuth: true, role: 'teacher' },
    children: [
      {
        path: 'courses',
        name: 'TeacherCourses',
        component: () => import('@/views/teacher/Courses.vue'),
      },
      {
        path: 'create',
        name: 'TeacherCreateCourse',
        component: () => import('@/views/teacher/CreateCourse.vue'),
      },
      {
        path: 'edit/:id',
        name: 'TeacherEditCourse',
        component: () => import('@/views/teacher/EditCourse.vue'),
      },
    ],
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('@/views/admin/Layout.vue'),
    meta: { requiresAuth: true, role: 'admin' },
    children: [
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/Users.vue'),
      },
      {
        path: 'courses',
        name: 'AdminCourses',
        component: () => import('@/views/admin/Courses.vue'),
      },
      {
        path: 'tags',
        name: 'AdminTags',
        component: () => import('@/views/admin/Tags.vue'),
      },
      {
        path: 'codes',
        name: 'AdminCodes',
        component: () => import('@/views/admin/Codes.vue'),
      },
      {
        path: 'reset-codes',
        name: 'AdminResetCodes',
        component: () => import('@/views/admin/ResetCodes.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.meta.role && authStore.userType !== to.meta.role) {
    // Redirect to appropriate dashboard based on role
    if (authStore.userType === 'student') {
      next('/student/courses')
    } else if (authStore.userType === 'teacher') {
      next('/teacher/courses')
    } else if (authStore.userType === 'admin') {
      next('/admin/users')
    } else {
      next('/login')
    }
  } else {
    next()
  }
})

export default router

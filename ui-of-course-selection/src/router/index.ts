import { createRouter, createWebHistory } from 'vue-router';
import Login from '../views/Login.vue';
import { useAuthStore } from '@/stores/auth';

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/student',
    name: 'StudentDashboard',
    component: () => import('../views/student/Dashboard.vue'),
    meta: { requiresAuth: true, role: 'student' }
  },
  {
    path: '/student/course/:id',
    name: 'StudentCourseDetail',
    component: () => import('../views/student/CourseDetail.vue'),
    meta: { requiresAuth: true, role: 'student' }
  },
  {
    path: '/teacher',
    name: 'TeacherDashboard',
    component: () => import('../views/teacher/Dashboard.vue'),
    meta: { requiresAuth: true, role: 'teacher' }
  },
  {
    path: '/teacher/course/:id',
    name: 'TeacherCourseDetail',
    component: () => import('../views/teacher/CourseDetail.vue'),
    meta: { requiresAuth: true, role: 'teacher' }
  },
  {
    path: '/admin',
    name: 'AdminDashboard',
    component: () => import('../views/admin/Dashboard.vue'),
    meta: { requiresAuth: true, role: 'admin' }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/NotFound.vue')
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return next({ name: 'Login' });
  }

  // This is a simple role check. It can be expanded later.
  if (to.meta.requiresAuth && to.meta.role && authStore.user?.user_type !== to.meta.role) {
      // For now, just redirect to login. A proper "unauthorized" page would be better.
      return next({ name: 'Login' });
  }

  next();
});

export default router;
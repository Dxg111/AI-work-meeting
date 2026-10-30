/**
 * Vue Router 配置
 */
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', public: true }
  },
  {
    path: '/stats',
    name: 'StatsDashboard',
    component: () => import('@/views/StatsDashboard.vue'),
    meta: { title: '统计首页' }
  },
  {
    path: '/',
    name: 'MeetingList',
    component: () => import('@/views/MeetingList.vue'),
    meta: { title: '会议列表' }
  },
  {
    path: '/meeting/:id',
    name: 'MeetingDetail',
    component: () => import('@/views/MeetingDetail.vue'),
    meta: { title: '会议详情' }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/Profile.vue'),
    meta: { title: '个人中心' }
  },
  {
    path: '/depts',
    name: 'DeptManagement',
    component: () => import('@/views/DeptManagement.vue'),
    meta: { title: '部门管理', requiresAdmin: true }
  },
  {
    path: '/users',
    name: 'UserManagement',
    component: () => import('@/views/UserManagement.vue'),
    meta: { title: '用户管理', requiresAdmin: true }
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫：未登录统一跳转登录页
router.beforeEach((to, from, next) => {
  document.title = to.meta.title
    ? `${to.meta.title} · 智能会议纪要助手系统`
    : '智能会议纪要助手系统'

  const token = localStorage.getItem('token')

  if (to.meta.public) {
    // 已登录用户访问登录页时直接进入统计首页
    if (token && to.name === 'Login') {
      return next('/stats')
    }
    return next()
  }

  if (!token) {
    return next({ path: '/login', query: { redirect: to.fullPath } })
  }

  // 后台管理页面仅超级管理员可访问
  if (to.meta.requiresAdmin) {
    let user = null
    try {
      user = JSON.parse(localStorage.getItem('user') || 'null')
    } catch (error) {
      user = null
    }
    if (!user || user.role !== 'super_admin') {
      return next('/stats')
    }
  }

  next()
})

export default router

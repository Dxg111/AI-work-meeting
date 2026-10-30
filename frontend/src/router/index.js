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
// vue-router 5 推荐直接 return 目标路由，不再使用 next()
router.beforeEach((to) => {
  document.title = to.meta.title
    ? `${to.meta.title} · 智能会议纪要助手系统`
    : '智能会议纪要助手系统'

  const token = localStorage.getItem('token')

  let user = null
  try {
    user = JSON.parse(localStorage.getItem('user') || 'null')
  } catch (error) {
    user = null
  }

  if (to.meta.public) {
    // 已登录用户访问登录页时直接进入首页；首次登录先改密码
    if (token && to.name === 'Login') {
      return user?.must_change_password ? '/profile' : '/stats'
    }
    return true
  }

  if (!token) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  // 首次登录/管理员重置密码后，必须先修改密码
  if (user?.must_change_password && !['/profile', '/login'].includes(to.path)) {
    return '/profile'
  }

  // 后台管理页面仅超级管理员可访问
  if (to.meta.requiresAdmin) {
    if (!user || user.role !== 'super_admin') {
      return '/stats'
    }
  }

  return true
})

export default router

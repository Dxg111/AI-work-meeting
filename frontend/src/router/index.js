/**
 * Vue Router 配置
 */
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
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
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title || '智能会议纪要助手系统'
  next()
})

export default router

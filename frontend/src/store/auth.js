/**
 * 登录状态管理
 */
import { defineStore } from 'pinia'
import { login as loginApi, getMe, logout as logoutApi } from '@/api/auth'

const TOKEN_KEY = 'token'
const USER_KEY = 'user'

function readStoredUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || 'null')
  } catch (error) {
    return null
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY) || '',
    user: readStoredUser()
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    displayName: (state) => state.user?.nickname || state.user?.username || '用户',
    isSuperAdmin: (state) => state.user?.role === 'super_admin'
  },

  actions: {
    /**
     * 登录并保存 token / 用户信息
     */
    async login(username, password) {
      const response = await loginApi({ username, password })
      const { token, user } = response.data

      this.token = token
      this.user = user
      localStorage.setItem(TOKEN_KEY, token)
      localStorage.setItem(USER_KEY, JSON.stringify(user))

      return response
    },

    /**
     * 刷新当前用户信息
     */
    async fetchMe() {
      const response = await getMe()
      this.user = response.data
      localStorage.setItem(USER_KEY, JSON.stringify(this.user))
      return response
    },

    /**
     * 退出登录（JWT 无状态，前端清除即可）
     */
    async logout() {
      try {
        await logoutApi()
      } catch (error) {
        // 网络异常或 token 已过期时忽略，继续清理本地状态
      }
      this.token = ''
      this.user = null
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    }
  }
})

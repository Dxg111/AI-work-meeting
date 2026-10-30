/**
 * Axios 实例配置
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'

const TOKEN_KEY = 'token'
const USER_KEY = 'user'

// 创建 axios 实例
const request = axios.create({
  baseURL: '/api',
  timeout: 60000, // 60秒超时（考虑到文件上传）
})

function clearAuthStorage() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

function redirectToLogin() {
  if (window.location.pathname.startsWith('/login')) {
    return
  }
  const current = window.location.pathname + window.location.search
  window.location.href = `/login?redirect=${encodeURIComponent(current)}`
}

// 请求拦截器：自动携带 JWT
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    const { code, message } = response.data

    if (code === 200) {
      // 返回完整信封 { code, message, data }，与 Store/页面调用方保持一致
      return response.data
    }

    if (code === 401) {
      clearAuthStorage()
      redirectToLogin()
    }

    ElMessage.error(message || '请求失败')
    return Promise.reject(new Error(message || '请求失败'))
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      const message = data?.message
      const isLoginRequest = (error.config?.url || '').includes('/auth/login')

      if (status === 401) {
        if (isLoginRequest) {
          // 登录失败：只提示，不跳转（本来就在登录页）
          ElMessage.error(message || '用户名或密码错误')
        } else {
          clearAuthStorage()
          ElMessage.error(message || '登录已过期，请重新登录')
          redirectToLogin()
        }
      } else if (status === 403) {
        ElMessage.error(message || '无权限访问')
      } else if (status === 404) {
        ElMessage.error(message || '请求的资源不存在')
      } else if (status === 500) {
        ElMessage.error(message || '服务器内部错误')
      } else {
        ElMessage.error(message || '请求失败')
      }
    } else if (error.request) {
      ElMessage.error('网络错误，请检查网络连接')
    } else {
      ElMessage.error('请求配置错误')
    }

    return Promise.reject(error)
  }
)

export default request

/**
 * 认证相关 API
 */
import request from './request'

/**
 * 登录
 */
export function login(data) {
  return request({
    url: '/auth/login',
    method: 'POST',
    data
  })
}

/**
 * 获取当前登录用户
 */
export function getMe() {
  return request({
    url: '/auth/me',
    method: 'GET'
  })
}

/**
 * 退出登录
 */
export function logout() {
  return request({
    url: '/auth/logout',
    method: 'POST'
  })
}

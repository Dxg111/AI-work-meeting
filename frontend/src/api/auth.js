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
 * 修改个人资料
 */
export function updateProfile(data) {
  return request({
    url: '/auth/profile',
    method: 'PUT',
    data
  })
}

/**
 * 修改本人密码
 */
export function changePassword(data) {
  return request({
    url: '/auth/password',
    method: 'PUT',
    data
  })
}

/**
 * 上传头像
 */
export function uploadAvatar(formData) {
  return request({
    url: '/auth/avatar',
    method: 'POST',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
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

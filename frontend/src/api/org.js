/**
 * 组织管理 API（部门 / 用户）
 */
import request from './request'

// ==================== 部门 ====================

export function getDeptList(params) {
  return request({
    url: '/org/depts',
    method: 'GET',
    params
  })
}

export function getDeptOptions() {
  return request({
    url: '/org/depts/options',
    method: 'GET'
  })
}

export function createDept(data) {
  return request({
    url: '/org/depts',
    method: 'POST',
    data
  })
}

export function updateDept(deptId, data) {
  return request({
    url: `/org/depts/${deptId}`,
    method: 'PUT',
    data
  })
}

export function deleteDept(deptId) {
  return request({
    url: `/org/depts/${deptId}`,
    method: 'DELETE'
  })
}

// ==================== 用户 ====================

export function getUserList(params) {
  return request({
    url: '/org/users',
    method: 'GET',
    params
  })
}

export function createUser(data) {
  return request({
    url: '/org/users',
    method: 'POST',
    data
  })
}

export function updateUser(userId, data) {
  return request({
    url: `/org/users/${userId}`,
    method: 'PUT',
    data
  })
}

export function updateUserStatus(userId, isActive) {
  return request({
    url: `/org/users/${userId}/status`,
    method: 'PUT',
    data: { is_active: isActive }
  })
}

export function resetUserPassword(userId, newPassword) {
  return request({
    url: `/org/users/${userId}/password`,
    method: 'PUT',
    data: { new_password: newPassword }
  })
}

export function deleteUser(userId) {
  return request({
    url: `/org/users/${userId}`,
    method: 'DELETE'
  })
}

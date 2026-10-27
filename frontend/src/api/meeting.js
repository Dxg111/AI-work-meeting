/**
 * 会议相关 API
 */
import request from './request'

/**
 * 健康检查
 */
export function healthCheck() {
  return request({
    url: '/health',
    method: 'get',
  })
}

/**
 * 上传会议
 */
export function uploadMeeting(data) {
  return request({
    url: '/meetings/upload',
    method: 'post',
    data,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}

/**
 * 获取会议列表
 */
export function getMeetingList(params) {
  return request({
    url: '/meetings',
    method: 'get',
    params,
  })
}

/**
 * 获取会议详情
 */
export function getMeetingDetail(id) {
  return request({
    url: `/meetings/${id}`,
    method: 'get',
  })
}

/**
 * 删除会议
 */
export function deleteMeeting(id) {
  return request({
    url: `/meetings/${id}`,
    method: 'delete',
  })
}

/**
 * 手动触发处理
 */
export function processMeeting(id) {
  return request({
    url: `/meetings/${id}/process`,
    method: 'post',
  })
}

/**
 * 发言人重命名
 */
export function renameSpeakers(id, data) {
  return request({
    url: `/meetings/${id}/speakers`,
    method: 'put',
    data,
  })
}

/**
 * 获取 Markdown 内容
 */
export function getMarkdown(id) {
  return request({
    url: `/meetings/${id}/markdown`,
    method: 'get',
  })
}

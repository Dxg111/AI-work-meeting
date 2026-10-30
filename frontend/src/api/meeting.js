/**
 * 会议管理 API
 */
import request from './request'

/**
 * 上传会议音视频
 */
export function uploadMeeting(data) {
  const formData = new FormData()
  formData.append('title', data.title)
  formData.append('file', data.file)
  formData.append('auto_process', data.auto_process)
  formData.append('share_dept', data.share_dept)

  return request({
    url: '/meetings/upload',
    method: 'POST',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 获取会议列表
 */
export function getMeetingList(params) {
  return request({
    url: '/meetings',
    method: 'GET',
    params
  })
}

/**
 * 获取会议详情
 */
export function getMeetingDetail(meetingId) {
  return request({
    url: `/meetings/${meetingId}`,
    method: 'GET'
  })
}

/**
 * 删除会议
 */
export function deleteMeeting(meetingId) {
  return request({
    url: `/meetings/${meetingId}`,
    method: 'DELETE'
  })
}

/**
 * 手动触发处理
 */
export function triggerProcess(meetingId) {
  return request({
    url: `/meetings/${meetingId}/process`,
    method: 'POST'
  })
}

/**
 * 重命名发言人
 */
export function renameSpeakers(meetingId, data) {
  return request({
    url: `/meetings/${meetingId}/speakers`,
    method: 'PUT',
    data
  })
}

/**
 * 获取 Markdown 纪要
 */
export function getMarkdown(meetingId) {
  return request({
    url: `/meetings/${meetingId}/markdown`,
    method: 'GET'
  })
}

/**
 * 修改分享设置
 */
export function updateShareSetting(meetingId, shareDept) {
  return request({
    url: `/meetings/${meetingId}/share`,
    method: 'PUT',
    params: { share_dept: shareDept }
  })
}

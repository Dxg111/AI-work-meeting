/**
 * 数据统计 API
 */
import request from './request'

export function getStats() {
  return request({
    url: '/stats',
    method: 'GET'
  })
}

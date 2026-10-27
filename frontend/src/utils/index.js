/**
 * 工具函数
 */

/**
 * 下载 Markdown 文件
 */
export function downloadMarkdown(content, filename) {
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * 格式化时间戳（毫秒）为 mm:ss 格式
 */
export function formatTime(ms) {
  const seconds = Math.floor(ms / 1000)
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
}

/**
 * 格式化日期时间
 */
export function formatDateTime(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  const year = date.getFullYear()
  const month = (date.getMonth() + 1).toString().padStart(2, '0')
  const day = date.getDate().toString().padStart(2, '0')
  const hour = date.getHours().toString().padStart(2, '0')
  const minute = date.getMinutes().toString().padStart(2, '0')
  const second = date.getSeconds().toString().padStart(2, '0')
  return `${year}-${month}-${day} ${hour}:${minute}:${second}`
}

/**
 * 会议状态映射
 */
export const STATUS_MAP = {
  uploaded: { label: '已上传', type: 'info' },
  transcribing: { label: '转写中', type: 'warning' },
  transcribed: { label: '已转写', type: 'success' },
  summarizing: { label: '生成中', type: 'warning' },
  done: { label: '已完成', type: 'success' },
  failed: { label: '失败', type: 'danger' },
}

/**
 * 获取状态标签
 */
export function getStatusLabel(status) {
  return STATUS_MAP[status]?.label || status
}

/**
 * 获取状态类型
 */
export function getStatusType(status) {
  return STATUS_MAP[status]?.type || 'info'
}

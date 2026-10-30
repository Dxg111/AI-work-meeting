/**
 * 文件下载工具
 */

/**
 * 下载文本文件
 * @param {String} content - 文件内容
 * @param {String} filename - 文件名
 * @param {String} mimeType - MIME 类型
 */
export function downloadTextFile(content, filename, mimeType = 'text/plain') {
  const blob = new Blob([content], { type: `${mimeType};charset=utf-8` })
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
 * 下载 Markdown 文件
 * @param {String} markdown - Markdown 内容
 * @param {String} filename - 文件名
 */
export function downloadMarkdown(markdown, filename) {
  downloadTextFile(markdown, filename, 'text/markdown')
}

/**
 * 格式化文件大小
 * @param {Number} bytes - 字节数
 * @returns {String}
 */
export function formatFileSize(bytes) {
  if (bytes === 0) return '0 B'

  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 格式化时长（秒）
 * @param {Number} seconds - 秒数
 * @returns {String}
 */
export function formatDuration(seconds) {
  if (!seconds || seconds < 0) return '00:00'

  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60

  if (hours > 0) {
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

/**
 * 格式化时间戳（毫秒）为 mm:ss
 * @param {Number} ms - 毫秒
 * @returns {String}
 */
export function formatTimestamp(ms) {
  const seconds = Math.floor(ms / 1000)
  return formatDuration(seconds)
}

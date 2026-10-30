/**
 * 日期时间格式化工具
 */

/**
 * 统一格式化为 YYYY-MM-DD HH:mm:ss
 * 兼容后端返回的 ISO 字符串（含 T 分隔符）
 */
export function formatDateTime(value) {
  if (!value) return '-'

  const text = String(value).replace('T', ' ')
  return text.length >= 19 ? text.slice(0, 19) : text
}

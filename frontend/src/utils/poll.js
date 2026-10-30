/**
 * 状态轮询工具
 */

/**
 * 轮询会议状态
 * @param {Function} fetchFn - 获取数据的函数
 * @param {Function} checkFn - 检查是否需要继续轮询的函数
 * @param {Number} interval - 轮询间隔（毫秒）
 * @param {Number} maxRetries - 最大轮询次数（0表示无限制）
 * @returns {Object} - 包含 start 和 stop 方法的对象
 */
export function createPoller(fetchFn, checkFn, interval = 5000, maxRetries = 0) {
  let timerId = null
  let retryCount = 0
  let isRunning = false

  const poll = async () => {
    if (!isRunning) return

    try {
      const result = await fetchFn()

      // 检查是否需要继续轮询
      const shouldContinue = checkFn(result)

      if (!shouldContinue) {
        stop()
        return
      }

      // 检查是否达到最大轮询次数
      retryCount++
      if (maxRetries > 0 && retryCount >= maxRetries) {
        console.log('[Poller] 达到最大轮询次数，停止轮询')
        stop()
        return
      }

      // 继续轮询
      if (isRunning) {
        timerId = setTimeout(poll, interval)
      }
    } catch (error) {
      console.error('[Poller] 轮询出错:', error)
      // 出错后继续轮询
      if (isRunning) {
        timerId = setTimeout(poll, interval)
      }
    }
  }

  const start = () => {
    if (isRunning) {
      console.warn('[Poller] 轮询已在运行中')
      return
    }

    isRunning = true
    retryCount = 0
    console.log('[Poller] 开始轮询')
    poll()
  }

  const stop = () => {
    if (!isRunning) return

    isRunning = false
    if (timerId) {
      clearTimeout(timerId)
      timerId = null
    }
    console.log('[Poller] 停止轮询')
  }

  return {
    start,
    stop,
    isRunning: () => isRunning
  }
}

/**
 * 检查会议是否处于处理中状态
 * @param {String} status - 会议状态
 * @returns {Boolean}
 */
export function isProcessingStatus(status) {
  return ['transcribing', 'summarizing'].includes(status)
}

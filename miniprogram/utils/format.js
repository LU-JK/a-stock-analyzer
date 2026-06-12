/**
 * 数字/价格格式化工具
 */

/**
 * 格式化价格 (保留2位小数)
 */
function formatPrice(n) {
  if (n == null || isNaN(n)) return '--'
  return Number(n).toFixed(2)
}

/**
 * 格式化涨跌幅 (+0.00%)
 */
function formatChangePct(n) {
  if (n == null || isNaN(n)) return '--'
  const sign = n > 0 ? '+' : ''
  return `${sign}${Number(n).toFixed(2)}%`
}

/**
 * 格式化涨跌额 (+0.00)
 */
function formatChange(n) {
  if (n == null || isNaN(n)) return '--'
  const sign = n > 0 ? '+' : ''
  return `${sign}${Number(n).toFixed(2)}`
}

/**
 * 涨跌颜色类名
 */
function colorClass(n) {
  if (n == null) return 'flat'
  if (n > 0) return 'up'
  if (n < 0) return 'down'
  return 'flat'
}

/**
 * 格式化大数 (亿/万)
 */
function formatBigNum(n) {
  if (n == null || isNaN(n)) return '--'
  const abs = Math.abs(n)
  if (abs >= 1e12) return (n / 1e12).toFixed(2) + '万亿'
  if (abs >= 1e8) return (n / 1e8).toFixed(2) + '亿'
  if (abs >= 1e4) return (n / 1e4).toFixed(1) + '万'
  return n.toFixed(0)
}

/**
 * 格式化成交量 (手)
 */
function formatVolume(n) {
  if (n == null || isNaN(n)) return '--'
  if (n >= 1e8) return (n / 1e8).toFixed(2) + '亿手'
  if (n >= 1e4) return (n / 1e4).toFixed(1) + '万手'
  return n + '手'
}

/**
 * 格式化市值
 */
function formatMarketCap(n) {
  return formatBigNum(n)
}

/**
 * 截断日期 (2026-06-11 -> 06-11)
 */
function shortDate(dateStr) {
  if (!dateStr) return ''
  return String(dateStr).slice(-5)
}

module.exports = {
  formatPrice,
  formatChangePct,
  formatChange,
  colorClass,
  formatBigNum,
  formatVolume,
  formatMarketCap,
  shortDate
}

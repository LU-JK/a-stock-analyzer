/**
 * API 请求封装 — 统一管理 wx.request
 */
const app = getApp()

/**
 * GET 请求
 * @param {string} path - API 路径 (如 '/stocks/search')
 * @param {object} params - 查询参数
 * @returns {Promise<any>}
 */
function get(path, params = {}) {
  const base = app.globalData.apiBase
  const query = Object.keys(params)
    .filter(k => params[k] !== undefined && params[k] !== null && params[k] !== '')
    .map(k => `${k}=${encodeURIComponent(params[k])}`)
    .join('&')

  const url = query ? `${base}${path}?${query}` : `${base}${path}`

  return new Promise((resolve, reject) => {
    wx.request({
      url,
      method: 'GET',
      timeout: 25000,
      success(res) {
        if (res.statusCode === 200) {
          resolve(res.data)
        } else {
          reject(new Error(`请求失败: ${res.statusCode}`))
        }
      },
      fail(err) {
        // 网络错误时给个友好提示
        if (err.errMsg.includes('timeout')) {
          reject(new Error('请求超时，请稍后重试'))
        } else if (err.errMsg.includes('fail')) {
          reject(new Error('网络连接失败，请检查后端服务是否启动'))
        } else {
          reject(new Error(err.errMsg || '请求失败'))
        }
      }
    })
  })
}

/**
 * 带缓存的 GET
 * @param {string} path
 * @param {object} params
 * @param {number} ttl - 缓存有效期 (秒)
 */
async function getCached(path, params = {}, ttl = 60) {
  const key = `cache:${path}:${JSON.stringify(params)}`
  try {
    const cached = wx.getStorageSync(key)
    if (cached && cached.time && (Date.now() - cached.time < ttl * 1000)) {
      return cached.data
    }
  } catch (e) { /* ignore */ }

  const data = await get(path, params)
  try {
    wx.setStorageSync(key, { data, time: Date.now() })
  } catch (e) { /* storage full */ }
  return data
}

module.exports = { get, getCached }

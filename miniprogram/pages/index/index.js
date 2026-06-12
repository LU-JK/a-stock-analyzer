const api = require('../../utils/api')
const { colorClass } = require('../../utils/format')

Page({
  data: {
    loading: true,
    meta: null,
    indices: [],
    topSectors: [],
    topGainers: [],
    signals: {},
    error: ''
  },

  onLoad() {
    this.fetchMarketData()
  },

  onPullDownRefresh() {
    this.fetchMarketData().then(() => wx.stopPullDownRefresh())
  },

  async fetchMarketData() {
    this.setData({ loading: true, error: '' })
    try {
      const data = await api.get('/market/overview')
      this.setData({
        meta: data.meta,
        indices: data.indices || [],
        topSectors: (data.top_sectors || []).slice(0, 5),
        topGainers: (data.top_gainers || []).slice(0, 8),
        signals: data.signals || {},
        loading: false
      })
    } catch (e) {
      this.setData({
        loading: false,
        error: e.message || '获取数据失败'
      })
    }
  },

  onTapSearch() {
    wx.navigateTo({ url: '/pages/search/search' })
  },

  onTapStock(e) {
    const code = e.currentTarget.dataset.code
    wx.navigateTo({ url: `/pages/detail/detail?code=${code}` })
  }
})

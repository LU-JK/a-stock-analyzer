App({
  globalData: {
    // API 地址 — 手机和电脑必须在同一WiFi下
    apiBase: 'http://192.168.145.99:8008/api/v1',
    // 缓存配置
    cacheExpiry: {
      market: 60,      // 市场数据 1分钟
      realtime: 30,    // 实时行情 30秒
      analysis: 3600   // 分析报告 1小时
    }
  },

  onLaunch() {
    // 检查网络状态
    wx.getNetworkType({
      success: (res) => {
        if (res.networkType === 'none') {
          wx.showToast({ title: '网络不可用', icon: 'none' })
        }
      }
    })
  }
})

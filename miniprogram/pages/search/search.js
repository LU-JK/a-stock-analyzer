const api = require('../../utils/api')

Page({
  data: {
    keyword: '',
    results: [],
    searching: false,
    searched: false,
    error: ''
  },

  // 防抖定时器
  _timer: null,

  onInput(e) {
    const keyword = e.detail.value.trim()
    this.setData({ keyword })

    // 300ms 防抖
    if (this._timer) clearTimeout(this._timer)
    if (!keyword) {
      this.setData({ results: [], searched: false })
      return
    }

    this._timer = setTimeout(() => {
      this.doSearch(keyword)
    }, 300)
  },

  async doSearch(keyword) {
    this.setData({ searching: true, error: '' })
    try {
      const data = await api.get('/stocks/search', { keyword, limit: 30 })
      this.setData({
        results: data.results || [],
        searching: false,
        searched: true
      })
    } catch (e) {
      this.setData({
        searching: false,
        searched: true,
        error: e.message || '搜索失败'
      })
    }
  },

  onClear() {
    this.setData({ keyword: '', results: [], searched: false, error: '' })
  },

  onTapStock(e) {
    const code = e.currentTarget.dataset.code
    wx.navigateTo({ url: `/pages/detail/detail?code=${code}` })
  }
})

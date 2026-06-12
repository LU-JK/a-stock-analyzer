const api = require('../../utils/api')
const fmt = require('../../utils/format')

Page({
  data: {
    code: '',
    // Tab
    activeTab: 0,
    tabs: ['概览', '技术', '财务', '分析'],

    // 概览
    quote: null,
    miniKline: [],

    // 技术
    technical: null,
    techLoading: false,

    // 财务
    financial: null,
    fundFlow: [],
    finLoading: false,

    // 分析
    analysis: null,
    analysisLoading: false,

    // 全局
    loading: true,
    error: ''
  },

  onLoad(options) {
    const code = options.code
    this.setData({ code })
    this.loadRealtime(code)
  },

  // ═══ 实时行情 ═══
  async loadRealtime(code) {
    this.setData({ loading: true, error: '' })
    try {
      const quote = await api.get(`/stocks/${code}/realtime`)
      this.setData({ quote, loading: false })

      // 预加载迷你K线
      this.loadMiniKline(code)
    } catch (e) {
      this.setData({ loading: false, error: e.message })
    }
  },

  async loadMiniKline(code) {
    try {
      const kline = await api.get(`/stocks/${code}/kline`, { days: 30 })
      this.setData({ miniKline: kline.data || [] })
    } catch (e) { /* 静默失败 */ }
  },

  // ═══ Tab 切换 ═══
  onTabChange(e) {
    const idx = e.currentTarget.dataset.index
    this.setData({ activeTab: idx })
    if (idx === 1 && !this.data.technical) this.loadTechnical()
    if (idx === 2 && !this.data.financial) this.loadFinancial()
    if (idx === 3 && !this.data.analysis) this.loadAnalysis()
  },

  // ═══ 技术指标 ═══
  async loadTechnical() {
    this.setData({ techLoading: true })
    try {
      const data = await api.get(`/stocks/${this.data.code}/technical`)
      this.setData({ technical: data, techLoading: false })
    } catch (e) {
      this.setData({ techLoading: false })
      wx.showToast({ title: '加载失败', icon: 'none' })
    }
  },

  // ═══ 财务数据 ═══
  async loadFinancial() {
    this.setData({ finLoading: true })
    try {
      const [fin, flow] = await Promise.all([
        api.get(`/stocks/${this.data.code}/financial`),
        api.get(`/stocks/${this.data.code}/fund-flow`, { days: 10 })
      ])
      this.setData({
        financial: fin,
        fundFlow: flow.data || [],
        finLoading: false
      })
    } catch (e) {
      this.setData({ finLoading: false })
      wx.showToast({ title: '加载失败', icon: 'none' })
    }
  },

  // ═══ 投资分析 ═══
  async loadAnalysis() {
    this.setData({ analysisLoading: true })
    try {
      const data = await api.get(`/stocks/${this.data.code}/analysis`)
      this.setData({ analysis: data, analysisLoading: false })
    } catch (e) {
      this.setData({ analysisLoading: false })
      wx.showToast({ title: '分析服务繁忙,请重试', icon: 'none' })
    }
  },

  // 格式化工具直接暴露给 WXML
  formatPrice: fmt.formatPrice,
  formatChangePct: fmt.formatChangePct,
  formatChange: fmt.formatChange,
  colorClass: fmt.colorClass,
  formatBigNum: fmt.formatBigNum,
  formatVolume: fmt.formatVolume,
  formatMarketCap: fmt.formatMarketCap
})

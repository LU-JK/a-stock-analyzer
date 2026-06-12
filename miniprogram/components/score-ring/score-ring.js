/**
 * 评分环 — Canvas 2D 绘制
 */
Component({
  properties: {
    score: { type: Number, value: 0 },  // 0-100
    size: { type: Number, value: 180 }   // rpx
  },

  data: {
    canvasId: 'score-canvas'
  },

  lifetimes: {
    attached() {
      this.draw()
    }
  },

  observers: {
    'score'() { this.draw() }
  },

  methods: {
    draw() {
      const query = this.createSelectorQuery()
      query.select('#scoreCanvas')
        .fields({ node: true, size: true })
        .exec((res) => {
          if (!res[0] || !res[0].node) return
          const canvas = res[0].node
          const ctx = canvas.getContext('2d')
          const dpr = wx.getSystemInfoSync().pixelRatio

          const size = this.properties.size
          canvas.width = size * dpr
          canvas.height = size * dpr
          ctx.scale(dpr, dpr)

          const cx = size / 2, cy = size / 2
          const radius = size / 2 - 12
          const score = this.properties.score

          // 背景环
          ctx.beginPath()
          ctx.arc(cx, cy, radius, 0, 2 * Math.PI)
          ctx.strokeStyle = '#2a2a40'
          ctx.lineWidth = 10
          ctx.stroke()

          // 分数环
          if (score > 0) {
            ctx.beginPath()
            const startAngle = -Math.PI / 2
            const endAngle = startAngle + (score / 100) * 2 * Math.PI
            ctx.arc(cx, cy, radius, startAngle, endAngle)
            const color = score >= 70 ? '#e63946' : score >= 40 ? '#f39c12' : '#2ecc71'
            ctx.strokeStyle = color
            ctx.lineWidth = 10
            ctx.lineCap = 'round'
            ctx.stroke()
          }

          // 分数文字
          ctx.fillStyle = '#fff'
          ctx.font = `bold ${size * 0.28}px -apple-system`
          ctx.textAlign = 'center'
          ctx.textBaseline = 'middle'
          ctx.fillText(String(score), cx, cy - 6)

          // "综合评分"
          ctx.fillStyle = '#888'
          ctx.font = `${size * 0.11}px -apple-system`
          ctx.fillText('综合评分', cx, cy + 24)
        })
    }
  }
})

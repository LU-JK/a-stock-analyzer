Component({
  properties: {
    code: { type: String, value: '' },
    name: { type: String, value: '' },
    price: { type: Number, value: 0 },
    changePct: { type: Number, value: 0 }
  },

  methods: {
    formatPrice(val) {
      if (val == null) return '--'
      return Number(val).toFixed(2)
    },
    formatPct(val) {
      if (val == null) return '--'
      const sign = val > 0 ? '+' : ''
      return sign + Number(val).toFixed(2) + '%'
    }
  }
})

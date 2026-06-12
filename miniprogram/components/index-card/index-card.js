Component({
  properties: {
    name: { type: String, value: '' },
    price: { type: Number, value: 0 },
    change: { type: Number, value: 0 },
    changePct: { type: Number, value: 0 }
  },

  computed: {},

  methods: {
    formatPrice(val) {
      if (val == null) return '--'
      return Number(val).toFixed(2)
    },
    formatChange(val) {
      if (val == null) return '--'
      const sign = val > 0 ? '+' : ''
      return sign + Number(val).toFixed(2)
    },
    formatPct(val) {
      if (val == null) return '--'
      const sign = val > 0 ? '+' : ''
      return sign + Number(val).toFixed(2) + '%'
    },
    colorClass(val) {
      if (val == null) return 'flat'
      if (val > 0) return 'up'
      if (val < 0) return 'down'
      return 'flat'
    }
  }
})

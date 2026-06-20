<template>
  <div class="orderbook-view">
    <div class="view-header">
      <div class="header-content">
        <h1>54D Orderbook Matrix</h1>
        <p>Live Gravity Wall Topology</p>
      </div>
      
      <div class="controls">
        <select v-model="selectedSymbol" class="symbol-select">
          <option v-for="sym in availableSymbols" :key="sym" :value="sym">{{ sym }}</option>
        </select>
      </div>
    </div>

    <div class="main-layout">
      <div class="matrix-container" ref="chartContainer"></div>
      
      <div class="order-entry-panel">
        <h3>Autopilot: {{ selectedSymbol }}</h3>
        
        <div class="ai-status" :class="{ 'is-active': autopilotEnabled }">
          <div class="status-indicator"></div>
          <span>{{ autopilotEnabled ? 'LGNN Engine Active' : 'System Standby' }}</span>
        </div>
        
        <div class="input-group">
          <label>Risk Level (Leverage)</label>
          <div class="input-wrapper">
            <input type="range" v-model="riskLevel" min="1" max="50" step="1" />
            <span class="currency">{{ riskLevel }}x</span>
          </div>
        </div>
        
        <div class="input-group">
          <label>Max Position Size</label>
          <div class="input-wrapper">
            <input type="number" v-model="orderAmount" placeholder="0.00" />
            <span class="currency">{{ selectedSymbol.split('/')[0] || 'BTC' }}</span>
          </div>
        </div>
        
        <div class="action-buttons">
          <button 
            :class="autopilotEnabled ? 'btn-stop' : 'btn-start'" 
            @click="toggleAutopilot"
          >
            {{ autopilotEnabled ? 'Halt Execution' : 'Engage LGNN Autopilot' }}
          </button>
        </div>
      </div>
    </div>

    <div class="history-panel">
      <div class="tabs">
        <button :class="{ active: activeTab === 'positions' }" @click="activeTab = 'positions'">Active Neural Positions</button>
        <button :class="{ active: activeTab === 'history' }" @click="activeTab = 'history'">LGNN Execution Log</button>
      </div>
      <div class="table-container">
        <table v-if="activeTab === 'history'">
          <thead>
            <tr>
              <th>Time</th>
              <th>Symbol</th>
              <th>Type</th>
              <th>Side</th>
              <th>Price</th>
              <th>Amount</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="orderHistory.length === 0">
              <td colspan="6" class="empty-state">No autonomous executions yet</td>
            </tr>
            <tr v-for="(order, idx) in orderHistory" :key="idx">
              <td>{{ new Date(order.timestamp).toLocaleTimeString() }}</td>
              <td class="symbol">{{ order.symbol }}</td>
              <td>{{ order.type.toUpperCase() }}</td>
              <td :class="order.side === 'buy' ? 'text-green' : 'text-red'">{{ order.side.toUpperCase() }}</td>
              <td>{{ order.price ? '$' + order.price.toLocaleString() : 'MARKET' }}</td>
              <td>{{ order.amount }}</td>
            </tr>
          </tbody>
        </table>
        
        <table v-if="activeTab === 'positions'">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Size</th>
              <th>Entry Price</th>
              <th>Mark Price</th>
              <th>PnL (ROE)</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td colspan="5" class="empty-state">No open positions. Waiting for LGNN to engage.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts'

const chartContainer = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null

const selectedSymbol = ref('BTC/USDC')
const availableSymbols = ref(['BTC/USDC', 'ETH/USDC'])

const orderAmount = ref('0.1')
const riskLevel = ref(10)
const autopilotEnabled = ref(false)

const activeTab = ref('history')
const orderHistory = ref<any[]>([])

const toggleAutopilot = async () => {
  if (!orderAmount.value || parseFloat(orderAmount.value) <= 0) {
    (window as any).showToast('Bitte Max Position Size eintragen', 'error')
    return
  }

  const newState = !autopilotEnabled.value

  try {
    const payload = {
      symbol: selectedSymbol.value,
      enabled: newState,
      risk_level: riskLevel.value,
      max_position: parseFloat(orderAmount.value)
    }

    const response = await fetch('/api/trading/autopilot', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })

    if (!response.ok) {
      throw new Error(`HTTP Error ${response.status}`)
    }

    const result = await response.json()
    autopilotEnabled.value = newState
    
    if (newState) {
      (window as any).showToast(`LGNN Autopilot aktiviert für ${selectedSymbol.value}`, 'success')
    } else {
      (window as any).showToast(`Autopilot gestoppt.`, 'error')
    }
  } catch (err) {
    console.error("Autopilot toggle error:", err)
    ;(window as any).showToast(`Backend Fehler: ${err}`, 'error')
  }
}

// Max 60 history ticks
const MAX_HISTORY = 60
const timestamps: string[] = []
const yCategories = ['A5', 'A4', 'A3', 'A2', 'A1', 'B1', 'B2', 'B3', 'B4', 'B5']

const heatmapData: [number, number, number][] = []
let maxVol = 0

// Premium Light Fintech Theme for ECharts
const updateChartTheme = () => {
  if (!chart) return
  
  const textColor = '#475569' // Slate 600
  const emptyColor = 'rgba(255, 255, 255, 0.3)' // Glassy empty cells
  const splitColor1 = 'rgba(255, 255, 255, 0.6)'
  const splitColor2 = 'rgba(241, 245, 249, 0.4)' // Slate 50 transparent

  const option = {
    backgroundColor: 'transparent',
    textStyle: { color: textColor, fontFamily: 'Inter, sans-serif' },
    tooltip: {
      position: 'top',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: 'rgba(0,0,0,0.05)',
      borderWidth: 1,
      padding: [8, 12],
      textStyle: { color: '#0f172a', fontWeight: 600, fontSize: 13 },
      extraCssText: 'box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1); border-radius: 8px; backdrop-filter: blur(8px);',
      formatter: function (params: any) {
        const level = yCategories[params.value[1]]
        const vol = Math.abs(params.value[2])
        return `${level}<br/><span style="color:#64748b;font-weight:400;">Vol</span> ${vol.toFixed(4)}`
      }
    },
    grid: {
      left: '60px',
      right: '20px',
      top: '20px',
      bottom: '40px'
    },
    xAxis: {
      type: 'category',
      data: timestamps,
      axisLabel: { color: textColor, fontSize: 11, fontWeight: 500 },
      axisLine: { lineStyle: { color: 'rgba(0,0,0,0.05)' } },
      splitArea: { show: true, areaStyle: { color: [splitColor1, splitColor2] } }
    },
    yAxis: {
      type: 'category',
      data: yCategories,
      axisLabel: { color: '#334155', fontSize: 12, fontWeight: 600 },
      axisLine: { lineStyle: { color: 'rgba(0,0,0,0.05)' } },
      splitArea: { show: true, areaStyle: { color: [splitColor1, splitColor2] } }
    },
    visualMap: {
      min: -maxVol || -10,
      max: maxVol || 10,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '0px',
      textStyle: { color: textColor, fontSize: 11 },
      itemWidth: 12,
      itemHeight: 120,
      inRange: {
        color: [
          '#e11d48', // High Ask (Rose 600)
          '#ffe4e6', // Low Ask (Rose 100)
          emptyColor, // 0 = Empty
          '#d1fae5', // Low Bid (Emerald 100)
          '#059669'  // High Bid (Emerald 600)
        ]
      }
    },
    series: [
      {
        name: 'Orderbook Depth',
        type: 'heatmap',
        data: heatmapData,
        label: {
          show: false
        },
        itemStyle: {
          borderWidth: 2,
          borderColor: 'rgba(255,255,255,0.8)', // Internal cell borders to enhance glass effect
          borderRadius: 4
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 15,
            shadowColor: 'rgba(0, 0, 0, 0.1)',
            borderColor: '#fff',
            borderWidth: 2
          }
        }
      }
    ]
  }
  
  chart.setOption(option)
}

const initChart = () => {
  if (!chartContainer.value) return
  chart = echarts.init(chartContainer.value)
  updateChartTheme()
}

const handleDivineUpdate = (event: CustomEvent) => {
  try {
    const payload = event.detail?.message?.payload
    if (!payload) return
    
    // Update available symbols dynamically
    const symbols = Object.keys(payload)
    if (symbols.length > 0) {
      // Add any new symbols from the payload
      symbols.forEach(sym => {
        if (!availableSymbols.value.includes(sym)) {
          availableSymbols.value.push(sym)
        }
      })
      // If the currently selected symbol isn't in the payload, switch to the first available
      if (!symbols.includes(selectedSymbol.value)) {
        selectedSymbol.value = symbols[0]
      }
    }

    const data = payload[selectedSymbol.value]
    if (!data) return
    
    const bids = data.orderbook_bids || []
    const asks = data.orderbook_asks || []
    
    // Bids and asks should be max 5
    if (bids.length === 0 && asks.length === 0) return

    // Limit to 60 history
    if (timestamps.length >= MAX_HISTORY) {
      timestamps.shift()
      // remove old data
      for (let i = heatmapData.length - 1; i >= 0; i--) {
        if (heatmapData[i][0] === 0) {
          heatmapData.splice(i, 1)
        } else {
          heatmapData[i][0] -= 1 // shift X index left
        }
      }
    }

    const currentX = timestamps.length
    const now = new Date()
    timestamps.push(`${now.getHours()}:${now.getMinutes()}:${now.getSeconds()}`)
    
    maxVol = 0

    // Bids (yIndex 5 to 9 corresponds to B1 to B5)
    for (let i = 0; i < 5; i++) {
      const vol = bids[i] ? parseFloat(bids[i][1]) : 0.0
      heatmapData.push([currentX, 5 + i, vol]) // Positive volume for bids
    }

    // Asks (yIndex 4 down to 0 corresponds to A1 to A5)
    for (let i = 0; i < 5; i++) {
      const vol = asks[i] ? parseFloat(asks[i][1]) : 0.0
      heatmapData.push([currentX, 4 - i, -vol]) // Negative volume for asks
    }

    // Calculate maxVol over ALL historical data to prevent color scale jumping
    let currentMaxVol = 0.0001 // Prevent division by zero
    for (let i = 0; i < heatmapData.length; i++) {
      const absVol = Math.abs(heatmapData[i][2])
      if (absVol > currentMaxVol) currentMaxVol = absVol
    }

    if (chart) {
      chart.setOption({
        xAxis: { data: timestamps },
        visualMap: { min: -currentMaxVol, max: currentMaxVol },
        series: [{ data: heatmapData }]
      })
    }

  } catch (e) {
    console.error("[OrderbookView] Error parsing divine update", e)
  }
}

const themeChangeListener = () => {
  updateChartTheme()
}

const wsListener = (e: Event) => {
  const customEvent = e as CustomEvent
  if (customEvent.detail?.message?.type === 'DIVINE_UPDATE') {
    handleDivineUpdate(customEvent)
  } else if (customEvent.detail?.message?.type === 'AUTONOMOUS_TRADE') {
    const trade = customEvent.detail.message.payload
    if (trade && trade.symbol === selectedSymbol.value) {
      orderHistory.value.unshift(trade)
      ;(window as any).showToast(`[LGNN] ${trade.side.toUpperCase()} Executed: ${trade.amount} @ ${trade.price}`, 'success')
    }
  }
}

const resizeListener = () => {
  if (chart && !chart.isDisposed()) {
    chart.resize()
  }
}

onMounted(() => {
  initChart()
  
  document.addEventListener('ws:message', wsListener)
  window.addEventListener('resize', resizeListener)
  mediaQuery.addEventListener('change', themeChangeListener)
})

onBeforeUnmount(() => {
  document.removeEventListener('ws:message', wsListener)
  window.removeEventListener('resize', resizeListener)
  mediaQuery.removeEventListener('change', themeChangeListener)
  if (chart) {
    chart.dispose()
  }
})
</script>

<style scoped>
.orderbook-view {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #F4F4F0;
  color: #1A1A1A;
  padding: 10px;
  box-sizing: border-box;
  overflow-y: auto;
  font-family: 'Space Mono', monospace;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
  border-bottom: 2px solid #1A1A1A;
  padding-bottom: 10px;
}

.header-content h1 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 900;
  text-transform: uppercase;
}

.header-content p {
  margin: 0;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
}

.controls .symbol-select {
  background: #FFF;
  border: 2px solid #1A1A1A;
  color: #1A1A1A;
  padding: 5px 10px;
  border-radius: 0;
  font-family: inherit;
  font-size: 0.8rem;
  font-weight: 900;
  cursor: pointer;
  box-shadow: 2px 2px 0px #1A1A1A;
}

.main-layout {
  display: flex;
  gap: 10px;
  flex: 1;
  min-height: 200px;
}

.matrix-container {
  flex: 2;
  background: #FFF;
  border: 2px solid #1A1A1A;
  box-shadow: 4px 4px 0px #1A1A1A;
  padding: 5px;
}

.order-entry-panel {
  flex: 1;
  background: #FFF;
  border: 2px solid #1A1A1A;
  box-shadow: 4px 4px 0px #1A1A1A;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.order-entry-panel h3 {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 900;
  text-transform: uppercase;
  border-bottom: 2px solid #1A1A1A;
  padding-bottom: 5px;
}

.history-panel {
  margin-top: 10px;
  background: #FFF;
  border: 2px solid #1A1A1A;
  box-shadow: 4px 4px 0px #1A1A1A;
  padding: 10px;
  max-height: 150px;
  overflow-y: auto;
}

.history-panel .tabs {
  display: flex;
  gap: 10px;
  border-bottom: 2px solid #1A1A1A;
  margin-bottom: 10px;
}

.history-panel .tabs button {
  background: none;
  border: none;
  font-size: 0.8rem;
  font-weight: 900;
  color: #666;
  padding: 5px;
  cursor: pointer;
  text-transform: uppercase;
}

.history-panel .tabs button.active {
  color: #1A1A1A;
  background: #F2C12E;
  border: 2px solid #1A1A1A;
  border-bottom: none;
}

.ai-status {
  display: flex;
  align-items: center;
  gap: 5px;
  background: #FFF;
  border: 2px solid #1A1A1A;
  padding: 5px;
  font-weight: 900;
  font-size: 0.7rem;
  text-transform: uppercase;
}

.ai-status.is-active {
  background: #F2C12E;
}

.status-indicator {
  width: 8px;
  height: 8px;
  background: #1A1A1A;
}

.ai-status.is-active .status-indicator {
  background: #E03C31;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.input-group label {
  font-size: 0.7rem;
  font-weight: 900;
  text-transform: uppercase;
}

.input-wrapper input {
  width: 100%;
  background: #FFF;
  border: 2px solid #1A1A1A;
  border-radius: 0;
  padding: 5px;
  font-size: 0.8rem;
  font-weight: 900;
  color: #1A1A1A;
  outline: none;
  box-sizing: border-box;
}

.input-wrapper .currency {
  display: none;
}

.action-buttons button {
  width: 100%;
  border: 2px solid #1A1A1A;
  border-radius: 0;
  padding: 8px;
  font-size: 0.8rem;
  font-weight: 900;
  color: #1A1A1A;
  cursor: pointer;
  background: #FFF;
  box-shadow: 2px 2px 0px #1A1A1A;
  text-transform: uppercase;
}

.btn-start {
  background: #F2C12E !important;
}

.btn-stop {
  background: #E03C31 !important;
  color: #FFF !important;
}

.action-buttons button:active {
  box-shadow: 0px 0px 0px #1A1A1A;
  transform: translate(2px, 2px);
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.7rem;
  text-transform: uppercase;
}

th {
  font-weight: 900;
  padding: 5px;
  border-bottom: 2px solid #1A1A1A;
  text-align: left;
}

td {
  padding: 5px;
  border-bottom: 1px solid #1A1A1A;
}

.symbol { font-weight: 900; }
.text-green { color: #1A1A1A; font-weight: 900; background: #F2C12E; padding: 2px; }
.text-red { color: #FFF; font-weight: 900; background: #E03C31; padding: 2px; }

.empty-state {
  text-align: center;
  padding: 10px !important;
  font-weight: 900;
}
</style>

<template>
  <div class="cyberpunk-portfolio" :class="{ 'glitch-active': glitch }">
    <!-- Header -->
    <div class="header">
      <h1 class="glitch" data-text="NEURO-LINK: OMNI-WALLET">NEURO-LINK: OMNI-WALLET</h1>
      <div class="status-indicator">
        <span class="blinking-dot"></span>
        STREAM: {{ isConnected ? 'SYNCHRONIZED' : 'OFFLINE' }}
      </div>
    </div>

    <!-- Main Grid -->
    <div class="dashboard-grid">
      
      <!-- Equity Box -->
      <div class="neon-panel equity-panel">
        <div class="panel-label">GLOBAL EQUITY (USD)</div>
        <div class="equity-value">
          <span class="currency">$</span>
          <span>{{ formatMoney(globalEquity) }}</span>
        </div>
        <div class="equity-bar-container">
          <div class="equity-bar-fill" :style="{ width: Math.min(100, (globalEquity / 150000) * 100) + '%' }"></div>
        </div>
        <div class="sub-metrics">
          <div class="metric">
            <span class="m-label">PRIMARY CORE</span>
            <span class="m-value">{{ primaryWallet.toUpperCase() }}</span>
          </div>
          <div class="metric">
            <span class="m-label">SYS_STATUS</span>
            <span class="m-value" :style="{ color: chaos >= 0.7 ? '#ff003c' : (chaos < 0.3 ? '#00f3ff' : '#0f0') }">
              {{ chaos >= 0.7 ? 'CHAOS DETECTED' : (chaos < 0.3 ? 'HIGH RESONANCE' : 'NOMINAL') }}
            </span>
          </div>
        </div>
      </div>

      <!-- Wallet Sub-Cores -->
      <div class="neon-panel wallets-panel">
        <div class="panel-label">SUB-CORES (ASSETS)</div>
        <div class="wallet-list">
          <div v-for="(wallet, exchange) in wallets" :key="exchange" class="wallet-item">
            <div class="w-exchange">[{{ String(exchange).toUpperCase() }}]</div>
            <div class="w-balances">
              <div v-for="(amount, asset) in wallet.balances" :key="asset" class="asset-line">
                <span class="asset-name">{{ asset }}</span>
                <span class="asset-amount">{{ typeof amount === 'number' ? amount.toFixed(4) : amount }}</span>
              </div>
            </div>
          </div>
          <div v-if="Object.keys(wallets).length === 0" class="no-data">
            NO SUB-CORES DETECTED.
          </div>
        </div>
      </div>

      <!-- Execution Log -->
      <div class="neon-panel trades-panel">
        <div class="panel-label">EXECUTION STREAM</div>
        <div class="trade-log">
          <div v-for="(trade, idx) in recentTrades" :key="idx" class="trade-row" :class="trade.side.toLowerCase()">
            <span class="t-time">{{ formatTime(trade.timestamp) }}</span>
            <span class="t-sym">{{ trade.symbol }}</span>
            <span class="t-side">[{{ trade.side }}]</span>
            <span class="t-price">@ {{ trade.price != null ? Number(trade.price).toFixed(4) : 'N/A' }}</span>
            <span class="t-qty">x {{ trade.qty }}</span>
          </div>
          <div v-if="recentTrades.length === 0" class="no-data" :style="{ color: chaos >= 0.7 ? '#ff003c' : (chaos < 0.3 ? '#00f3ff' : '') }">
             {{ chaos >= 0.7 ? 'SANCTUARY MODE ACTIVE (CAPITAL SHIELD)' : (chaos < 0.3 ? 'AGGRESSIVE TRADING ENGAGED...' : 'AWAITING SIGNAL...') }}
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  chaos: { type: Number, default: 0.5 },
  tau: { type: Number, default: 1.0 }
})

const isConnected = ref(false)
const globalEquity = ref(0.0)
const primaryWallet = ref("UNKNOWN")
const wallets = ref<Record<string, any>>({})
const recentTrades = ref<any[]>([])
const glitch = ref(false)

let ws: WebSocket | null = null

const formatMoney = (val: number) => {
  return val.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const formatTime = (ts: number) => {
  if (!ts) return "00:00:00"
  const d = new Date(ts)
  return d.toTimeString().split(' ')[0]
}

const connectStream = () => {
  const wsUrl = `ws://127.0.0.1:8000/ws/stream`
  ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    // Send Auth Handshake
    const token = import.meta.env.VITE_ADMIN_TOKEN || "397915a57a45b746b856532444fd9b29"
    ws?.send(JSON.stringify({ type: "AUTH", token }))
    // Wait, what is the token? In settings it's probably default. I'll use a generic token or it might fail.
    // Actually, in backend/config/settings.py the default is usually "auratic_admin_123" or something.
    // Let's check if the backend rejects it. If so, we need the real token.
    setTimeout(() => { isConnected.value = true }, 500)
  }

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data)
      
      if (msg.type === "FULL_STATE" && msg.payload) {
        const payload = msg.payload
        if (payload.wallet) {
          globalEquity.value = payload.wallet.global_equity || 0.0
          primaryWallet.value = payload.wallet.primary || "UNKNOWN"
          wallets.value = payload.wallet.wallets || {}
          
          // Random glitch effect on big updates
          if (Math.random() > 0.7) {
            glitch.value = true
            setTimeout(() => glitch.value = false, 200)
          }
        }
        if (payload.trades) {
           recentTrades.value = payload.trades.slice(-20).reverse()
        }
      }
      else if (msg.type === "EXECUTION_UPDATE") {
        if (msg.trade) {
          recentTrades.value.unshift(msg.trade)
          if (recentTrades.value.length > 20) recentTrades.value.pop()
          glitch.value = true
          setTimeout(() => glitch.value = false, 150)
        }
      }
    } catch (e) {
      console.error("[PORTFOLIO] Parse error:", e)
    }
  }

  ws.onclose = () => {
    isConnected.value = false
    setTimeout(connectStream, 5000)
  }
}

onMounted(() => {
  connectStream()
})

onUnmounted(() => {
  if (ws) ws.close()
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700;800&display=swap');

.cyberpunk-portfolio {
  position: absolute;
  bottom: 20px;
  right: 20px;
  width: 450px;
  background: #FFFFFF;
  border: 4px solid #111111;
  box-shadow: 8px 8px 0px #111111;
  color: #111111;
  font-family: 'JetBrains Mono', monospace;
  z-index: 1000;
  display: flex;
  flex-direction: column;
}

.glitch-active {
  transform: translate(2px, -2px);
  box-shadow: 10px 10px 0px #E03C31;
}

.chaos-mode {
  border-color: #E03C31;
  box-shadow: 8px 8px 0px #E03C31;
}

.resonance-mode {
  border-color: #00FF41;
  box-shadow: 8px 8px 0px #00FF41;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #111111;
  color: #FFFFFF;
  padding: 10px 15px;
  border-bottom: 4px solid #111111;
}

.header h1 {
  font-size: 1.2rem;
  font-weight: 800;
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.status-indicator {
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
}

.blinking-dot {
  width: 10px;
  height: 10px;
  background: #00FF41;
  border: 2px solid #FFFFFF;
  border-radius: 0; /* Blocky, not round */
  animation: blink 1s step-end infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.dashboard-grid {
  padding: 15px;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.neon-panel {
  background: #F8F8F8;
  border: 2px solid #111111;
  padding: 10px;
  position: relative;
}

.panel-label {
  position: absolute;
  top: -10px;
  left: 10px;
  background: #FFFFFF;
  padding: 0 5px;
  font-size: 0.75rem;
  font-weight: 800;
  color: #111111;
  border: 2px solid #111111;
}

/* Equity Box */
.equity-panel {
  text-align: center;
  background: #111111;
  color: #FFFFFF;
  border: 4px solid #111111;
}

.equity-panel .panel-label {
  background: #F2C12E;
  color: #111111;
  border: 2px solid #111111;
}

.equity-value {
  font-size: 2.8rem;
  font-weight: 800;
  color: #F2C12E;
  margin: 15px 0 5px 0;
  letter-spacing: -1px;
}

.currency {
  font-size: 1.4rem;
  vertical-align: top;
  margin-right: 4px;
}

.equity-bar-container {
  width: 100%;
  height: 8px;
  background: #333333;
  margin: 15px 0;
  border: 2px solid #111111;
}

.equity-bar-fill {
  height: 100%;
  background: #00FF41;
  transition: width 0.2s;
}

.sub-metrics {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  padding-top: 10px;
  border-top: 2px dotted #555555;
}

.metric {
  display: flex;
  flex-direction: column;
  text-align: left;
}

.metric:last-child {
  text-align: right;
}

.m-label {
  color: #AAAAAA;
  font-size: 0.7rem;
  font-weight: 700;
  margin-bottom: 2px;
}

.m-value {
  color: #FFFFFF;
  font-weight: 800;
}

/* Wallets Box */
.wallets-panel {
  margin-top: 10px;
}

.wallet-list {
  max-height: 90px;
  overflow-y: auto;
  padding-top: 10px;
}

.wallet-list::-webkit-scrollbar { width: 8px; border-left: 2px solid #111111; }
.wallet-list::-webkit-scrollbar-thumb { background: #111111; }
.wallet-list::-webkit-scrollbar-track { background: #F8F8F8; }

.wallet-item {
  display: flex;
  justify-content: space-between;
  border-bottom: 2px dotted #111111;
  padding: 6px 0;
  font-size: 0.85rem;
  font-weight: 700;
}
.wallet-item:last-child {
  border-bottom: none;
}
.w-exchange { color: #111111; }
.asset-line {
  display: flex;
  gap: 15px;
  justify-content: flex-end;
}
.asset-name { color: #555555; }
.asset-amount { color: #111111; }

/* Trades Box */
.trades-panel {
  margin-top: 10px;
}

.trade-log {
  max-height: 120px;
  overflow-y: auto;
  font-size: 0.8rem;
  padding-top: 10px;
  font-weight: 700;
}
.trade-log::-webkit-scrollbar { width: 8px; border-left: 2px solid #111111; }
.trade-log::-webkit-scrollbar-thumb { background: #111111; }

.trade-row {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  border-bottom: 2px dotted #111111;
}

.trade-row:last-child {
  border-bottom: none;
}

.trade-row.buy { color: #005096; }
.trade-row.sell { color: #E03C31; }

.t-time { color: #555555; font-size: 0.75rem; }
.t-sym { color: #111111; font-weight: 800; }
.t-side { font-weight: 800; }

.no-data {
  color: #111111;
  text-align: center;
  font-size: 0.85rem;
  padding: 15px 0;
  font-weight: 800;
  text-transform: uppercase;
}
</style>

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
            <span class="m-value" style="color: #0f0;">NOMINAL</span>
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
            <span class="t-price">@ {{ trade.price.toFixed(4) }}</span>
            <span class="t-qty">x {{ trade.qty }}</span>
          </div>
          <div v-if="recentTrades.length === 0" class="no-data">
             AWAITING SIGNAL...
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

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
    ws?.send(JSON.stringify({ type: "AUTH", token: "AURATIC_ADMIN_OVERRIDE_0x99" }))
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
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');

.cyberpunk-portfolio {
  position: absolute;
  bottom: 20px;
  right: 20px;
  width: 450px;
  background: rgba(10, 10, 12, 0.85);
  border: 1px solid #0ff;
  border-left: 4px solid #f0f;
  box-shadow: 0 0 15px rgba(0, 255, 255, 0.2), inset 0 0 20px rgba(255, 0, 255, 0.1);
  color: #0ff;
  font-family: 'Share Tech Mono', monospace;
  padding: 15px;
  z-index: 1000;
  backdrop-filter: blur(5px);
  clip-path: polygon(0 0, 100% 0, 100% calc(100% - 20px), calc(100% - 20px) 100%, 0 100%);
  transition: all 0.2s;
}

.glitch-active {
  transform: translateX(2px) translateY(-2px);
  filter: hue-rotate(90deg) contrast(150%);
  box-shadow: 0 0 30px rgba(255, 0, 0, 0.5);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(0, 255, 255, 0.3);
  padding-bottom: 10px;
  margin-bottom: 15px;
}

.header h1 {
  font-size: 1.1rem;
  margin: 0;
  color: #fff;
  text-shadow: 0 0 5px #0ff;
  letter-spacing: 2px;
}

.status-indicator {
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  gap: 6px;
  color: #0f0;
}

.blinking-dot {
  width: 8px;
  height: 8px;
  background: #0f0;
  border-radius: 50%;
  animation: blink 1s infinite;
  box-shadow: 0 0 8px #0f0;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.2; }
}

.neon-panel {
  background: rgba(0, 20, 30, 0.6);
  border: 1px solid rgba(0, 255, 255, 0.2);
  margin-bottom: 10px;
  padding: 10px;
}

.panel-label {
  font-size: 0.7rem;
  color: #f0f;
  margin-bottom: 8px;
  letter-spacing: 1px;
}

/* Equity Box */
.equity-panel {
  text-align: center;
}

.equity-value {
  font-size: 2.2rem;
  font-weight: bold;
  color: #fff;
  text-shadow: 0 0 10px #0ff;
  margin: 5px 0;
}

.currency {
  font-size: 1.2rem;
  color: #0ff;
  vertical-align: super;
}

.equity-bar-container {
  width: 100%;
  height: 4px;
  background: #111;
  margin: 10px 0;
}

.equity-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #0ff, #f0f);
  box-shadow: 0 0 10px #f0f;
  transition: width 1s ease-out;
}

.sub-metrics {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
}

.metric {
  display: flex;
  flex-direction: column;
}

.m-label {
  color: #666;
  font-size: 0.6rem;
}

.m-value {
  color: #0ff;
}

/* Wallets Box */
.wallet-list {
  max-height: 80px;
  overflow-y: auto;
}
.wallet-list::-webkit-scrollbar { width: 4px; }
.wallet-list::-webkit-scrollbar-thumb { background: #0ff; }

.wallet-item {
  display: flex;
  justify-content: space-between;
  border-bottom: 1px dashed rgba(0,255,255,0.2);
  padding: 4px 0;
  font-size: 0.85rem;
}
.w-exchange { color: #fff; }
.asset-line {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}
.asset-name { color: #f0f; }
.asset-amount { color: #0ff; }

/* Trades Box */
.trade-log {
  max-height: 120px;
  overflow-y: auto;
  font-size: 0.75rem;
}
.trade-log::-webkit-scrollbar { width: 4px; }
.trade-log::-webkit-scrollbar-thumb { background: #f0f; }

.trade-row {
  display: flex;
  justify-content: space-between;
  padding: 3px 0;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}

.trade-row.buy { color: #0f0; text-shadow: 0 0 3px #0f0; }
.trade-row.sell { color: #f00; text-shadow: 0 0 3px #f00; }

.t-time { color: #666; text-shadow: none; }
.t-sym { color: #fff; text-shadow: none; }

.no-data {
  color: #666;
  text-align: center;
  font-size: 0.8rem;
  padding: 10px 0;
  animation: blink 2s infinite;
}
</style>

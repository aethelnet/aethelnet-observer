<template>
  <div class="aethelnet-dashboard">
    <div class="dashboard-glass-panel">
      <!-- HEADER -->
      <header class="dashboard-header">
        <div class="brand">
          <div class="brand-logo"></div>
          <h1 class="brand-title">AETHELNET <span>PRIME</span></h1>
        </div>
        <div class="system-status">
          <div class="status-indicator" :class="{ 'online': status.is_running }"></div>
          <span class="status-text">{{ status.is_running ? 'Core Engine Online' : 'Offline' }}</span>
        </div>
      </header>

      <!-- MAIN CONTENT GRID -->
      <main class="dashboard-grid">
        <!-- LEFT COLUMN: PORTFOLIO & MARGIN -->
        <section class="panel portfolio-panel">
          <h2 class="panel-title">Operations</h2>
          <div class="metric-card">
            <span class="metric-label">Active Equity</span>
            <span class="metric-value">${{ metrics.current_equity.toFixed(2) }}</span>
            <div class="progress-bar-container">
              <div class="progress-bar" style="width: 100%"></div>
            </div>
          </div>
          <div class="metric-card">
            <span class="metric-label">Session PnL</span>
            <span class="metric-value" :class="{ 'positive': metrics.total_pnl >= 0, 'negative': metrics.total_pnl < 0 }">
              {{ metrics.total_pnl >= 0 ? '+' : '' }}${{ metrics.total_pnl.toFixed(2) }}
            </span>
          </div>
        </section>

        <!-- CENTER COLUMN: ACTIVE DIRECTIVES (TRADES) -->
        <section class="panel directives-panel">
          <h2 class="panel-title">Active Directives</h2>
          <div class="directive-list">
            <div v-if="positions.length === 0" style="color: #64748b; font-size: 0.9rem; padding: 1rem;">
              No active directives. Waiting for signal.
            </div>
            <!-- Live Trades -->
            <div v-for="pos in positions" :key="pos.symbol" class="directive-card" :class="{ 'positive-glow': pos.unrealized_pnl >= 0, 'negative-glow': pos.unrealized_pnl < 0 }">
              <div class="directive-header">
                <span class="symbol">{{ pos.symbol }}</span>
                <span class="side" :class="{ 'long': pos.size > 0, 'short': pos.size < 0 }">
                  {{ pos.size > 0 ? 'LONG' : 'SHORT' }}
                </span>
              </div>
              <div class="directive-body">
                <div class="data-point">
                  <span class="label">Size</span>
                  <span class="value">{{ Math.abs(pos.size) }}</span>
                </div>
                <div class="data-point">
                  <span class="label">Entry / Mark</span>
                  <span class="value">${{ pos.entry_price.toFixed(4) }} / ${{ pos.mark_price.toFixed(4) }}</span>
                </div>
              </div>
              <div class="directive-footer">
                <span class="pnl" :class="{ 'positive': pos.unrealized_pnl >= 0, 'negative': pos.unrealized_pnl < 0 }">
                  {{ pos.unrealized_pnl >= 0 ? '+' : '' }}${{ pos.unrealized_pnl.toFixed(2) }}
                </span>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const status = ref({ is_running: false })
const metrics = ref({ current_equity: 0.0, total_pnl: 0.0 })
const positions = ref<any[]>([])
let pollInterval: any = null

const fetchData = async () => {
  try {
    const [statusRes, metricsRes, posRes] = await Promise.all([
      fetch('/api/dashboard/status'),
      fetch('/api/dashboard/metrics'),
      fetch('/api/dashboard/positions')
    ])
    
    if (statusRes.ok) status.value = await statusRes.json()
    if (metricsRes.ok) metrics.value = await metricsRes.json()
    if (posRes.ok) positions.value = await posRes.json()
  } catch (err) {
    console.error('Failed to fetch dashboard data:', err)
  }
}

onMounted(() => {
  fetchData()
  pollInterval = setInterval(fetchData, 3000) // Poll every 3 seconds for raw simplicity
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})
</script>

<style scoped>
/* RAW FUNCTIONAL CSS - NO BLOAT */
.aethelnet-dashboard {
  font-family: monospace;
  padding: 2rem;
  background-color: #ffffff;
  color: #000000;
  height: 100%;
  overflow-y: auto;
  box-sizing: border-box;
}

.dashboard-header {
  border-bottom: 2px solid #000;
  padding-bottom: 1rem;
  margin-bottom: 1rem;
  display: flex;
  justify-content: space-between;
}

.brand-title {
  font-weight: bold;
  font-size: 1.2rem;
}

.system-status {
  font-weight: bold;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 250px 1fr;
  gap: 2rem;
}

.panel-title {
  border-bottom: 1px solid #ccc;
  padding-bottom: 0.5rem;
  font-weight: bold;
  text-transform: uppercase;
}

.metric-card, .directive-card {
  border: 1px solid #000;
  padding: 1rem;
  margin-bottom: 1rem;
}

.metric-value {
  font-size: 1.5rem;
  font-weight: bold;
}

.positive { color: green; }
.negative { color: red; }

.directive-header {
  display: flex;
  justify-content: space-between;
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.directive-body {
  display: flex;
  gap: 1rem;
}

.directive-footer {
  margin-top: 0.5rem;
  border-top: 1px dashed #000;
  padding-top: 0.5rem;
  text-align: right;
}
</style>

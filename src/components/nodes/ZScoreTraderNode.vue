<template>
  <div class="z-score-trader-node">
    <div class="z-header">
      <span class="z-icon">🎯</span> Z-Score Sniper Engine
    </div>
    <div class="z-content">
      <div class="z-status" :class="{ active: status.is_running }">
        {{ status.is_running ? '🟢 Engine ONLINE' : '🔴 Engine OFFLINE' }}
      </div>
      <div class="z-metrics">
        <div class="z-metric">
          <span class="z-label">Equity</span>
          <span class="z-value">${{ metrics.current_equity.toFixed(2) }}</span>
        </div>
        <div class="z-metric">
          <span class="z-label">Session PnL</span>
          <span class="z-value" :class="{ 'pos': metrics.total_pnl >= 0, 'neg': metrics.total_pnl < 0 }">
            {{ metrics.total_pnl >= 0 ? '+' : '' }}${{ metrics.total_pnl.toFixed(2) }}
          </span>
        </div>
      </div>
      
      <div class="z-positions">
        <div class="z-pos-title">Active Directives</div>
        <div v-if="positions.length === 0" class="z-no-pos">No active trades. Sniper scanning...</div>
        <div v-for="pos in positions" :key="pos.symbol" class="z-pos">
          <div class="z-pos-head">
            <span class="z-symbol">{{ pos.symbol }}</span>
            <span class="z-side" :class="pos.size > 0 ? 'pos' : 'neg'">{{ pos.size > 0 ? 'LONG' : 'SHORT' }}</span>
          </div>
          <div class="z-pos-pnl" :class="{ 'pos': pos.unrealized_pnl >= 0, 'neg': pos.unrealized_pnl < 0 }">
            {{ pos.unrealized_pnl >= 0 ? '+' : '' }}${{ pos.unrealized_pnl.toFixed(2) }}
          </div>
        </div>
      </div>
    </div>
    
    <div class="z-footer">
      <button @click="$emit('close')" class="z-btn">Collapse</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  node: { type: Object, required: true }
})
defineEmits(['close', 'content-updated', 'metadata-updated'])

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
  pollInterval = setInterval(fetchData, 3000)
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})
</script>

<style scoped>
.z-score-trader-node {
  width: 100%;
  height: 100%;
  background: rgba(10, 10, 10, 0.95);
  border: 1px solid #333;
  color: #fff;
  display: flex;
  flex-direction: column;
  font-family: monospace;
}
.z-header {
  padding: 8px;
  background: #1a1a1a;
  border-bottom: 1px solid #333;
  font-weight: bold;
  display: flex;
  align-items: center;
  gap: 8px;
}
.z-icon { font-size: 1.2rem; }
.z-content {
  flex: 1;
  padding: 12px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.z-status {
  padding: 6px;
  background: #331111;
  color: #ff4444;
  border-radius: 4px;
  text-align: center;
  font-weight: bold;
}
.z-status.active {
  background: #113311;
  color: #44ff44;
}
.z-metrics {
  display: flex;
  gap: 8px;
}
.z-metric {
  flex: 1;
  background: #222;
  padding: 8px;
  border-radius: 4px;
}
.z-label {
  display: block;
  font-size: 0.8rem;
  color: #888;
}
.z-value {
  display: block;
  font-size: 1.1rem;
  font-weight: bold;
}
.pos { color: #44ff44; }
.neg { color: #ff4444; }
.z-positions {
  border: 1px solid #333;
  border-radius: 4px;
  padding: 8px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.z-pos-title { font-weight: bold; font-size: 0.9rem; color: #ccc; border-bottom: 1px solid #333; padding-bottom: 4px; }
.z-no-pos { color: #666; font-size: 0.9rem; }
.z-pos {
  display: flex;
  justify-content: space-between;
  background: #1a1a1a;
  padding: 8px;
  border-radius: 4px;
}
.z-pos-head { display: flex; gap: 8px; font-weight: bold; }
.z-pos-pnl { font-weight: bold; }
.z-footer {
  padding: 8px;
  border-top: 1px solid #333;
  display: flex;
  justify-content: flex-end;
}
.z-btn {
  background: #333;
  color: #fff;
  border: none;
  padding: 4px 12px;
  border-radius: 4px;
  cursor: pointer;
}
.z-btn:hover { background: #444; }
</style>

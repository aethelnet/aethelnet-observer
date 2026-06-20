<template>
  <div class="pattern-matcher-node">
    <div class="header">
      <span class="icon">🦂</span>
      <span class="title">EPISODE PATTERN MATCHER</span>
      <span class="badge" :class="{'is-updating': isUpdating}">
        {{ isUpdating ? 'FORGING' : 'ACTIVE' }}
      </span>
    </div>
    
    <div class="body">
      <p class="desc">
        Identifies successful historical episodes and matches live z-score, volatility, and momentum signatures.
      </p>

      <div class="actions">
        <button class="action-btn" @click="triggerUpdate" :disabled="isUpdating">
          {{ isUpdating ? 'RUNNING FORGE...' : 'RE-FORGE PATTERNS' }}
        </button>
      </div>

      <div v-if="loading" class="status-msg">
        <span class="pulse">●</span> Loading Memory...
      </div>
      
      <div v-else-if="patterns.length === 0" class="status-msg empty">
        No patterns loaded. Tabula Rasa.
      </div>
      
      <div v-else class="patterns-list">
        <div class="summary-info">
          <span>Patterns: {{ patterns.length }}</span>
          <span v-if="lastAnalysis" class="timestamp">Last: {{ formattedTime }}</span>
        </div>
        <div class="scroll-area">
          <table class="patterns-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Regime</th>
                <th>Avg PnL</th>
                <th>Success</th>
                <th>Count</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="pat in patterns" :key="pat.id" class="pattern-row">
                <td class="pat-id" :title="pat.id">{{ pat.id }}</td>
                <td class="pat-regime">{{ pat.regime }}</td>
                <td class="pat-pnl" :style="{ color: pat.avg_pnl_pct >= 0 ? '#00FF41' : '#E03C31' }">
                  {{ pat.avg_pnl_pct.toFixed(2) }}%
                </td>
                <td class="pat-success">{{ (pat.success_rate * 100).toFixed(0) }}%</td>
                <td class="pat-count">{{ pat.sample_count }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'

const props = defineProps<{
  node: any
  globalNodes?: any[]
  globalLinks?: any[]
}>()

const patterns = ref<any[]>([])
const loading = ref(true)
const isUpdating = ref(false)
const lastAnalysis = ref<string | null>(null)

const API_BASE = (window as any).API_BASE || ''

const formattedTime = computed(() => {
  if (!lastAnalysis.value) return ''
  try {
    const d = new Date(lastAnalysis.value)
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } catch (e) {
    return ''
  }
})

async function fetchPatterns() {
  try {
    const url = API_BASE ? `${API_BASE}/auto-discovery/patterns` : `/api/auto-discovery/patterns`
    const res = await fetch(url)
    if (res.ok) {
      const data = await res.json()
      patterns.value = data.patterns || []
      lastAnalysis.value = data.last_analysis || null
    }
  } catch (e) {
    console.error("Failed to fetch patterns:", e)
  } finally {
    loading.value = false
  }
}

async function triggerUpdate() {
  if (isUpdating.value) return
  isUpdating.value = true
  try {
    const url = API_BASE ? `${API_BASE}/auto-discovery/patterns/update` : `/api/auto-discovery/patterns/update`
    const res = await fetch(url, { method: 'POST' })
    if (res.ok) {
      // Background task started
      setTimeout(async () => {
        await fetchPatterns()
        isUpdating.value = false
      }, 5000)
    } else {
      isUpdating.value = false
    }
  } catch (e) {
    console.error("Failed to trigger patterns update:", e)
    isUpdating.value = false
  }
}

onMounted(() => {
  fetchPatterns()
})
</script>

<style scoped>
.pattern-matcher-node {
  width: 320px;
  background: rgba(10, 20, 30, 0.9);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 8px;
  color: #fff;
  font-family: 'Rajdhani', sans-serif;
  overflow: hidden;
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.1);
}

.header {
  background: linear-gradient(90deg, rgba(0,212,255,0.2) 0%, transparent 100%);
  padding: 12px;
  display: flex;
  align-items: center;
  border-bottom: 1px solid rgba(0, 212, 255, 0.2);
}

.icon {
  font-size: 1.2rem;
  margin-right: 8px;
}

.title {
  font-weight: 600;
  letter-spacing: 1px;
  color: #00d4ff;
  text-shadow: 0 0 5px rgba(0,212,255,0.5);
  flex-grow: 1;
  font-size: 0.95rem;
}

.badge {
  font-size: 0.7rem;
  background: #00d4ff;
  color: #000;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 900;
}

.badge.is-updating {
  background: #FF9800;
  animation: pulse-update 1.5s infinite;
}

@keyframes pulse-update {
  0% { opacity: 0.8; }
  50% { opacity: 1; }
  100% { opacity: 0.8; }
}

.body {
  padding: 16px;
}

.desc {
  font-size: 0.85rem;
  color: #aaa;
  margin-bottom: 16px;
  line-height: 1.4;
}

.actions {
  margin-bottom: 16px;
}

.action-btn {
  width: 100%;
  background: transparent;
  border: 1px solid #00d4ff;
  color: #00d4ff;
  padding: 8px;
  border-radius: 4px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s;
  font-family: 'Rajdhani', sans-serif;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.action-btn:hover:not(:disabled) {
  background: #00d4ff;
  color: #000;
  box-shadow: 0 0 10px rgba(0, 212, 255, 0.4);
}

.action-btn:disabled {
  border-color: #555;
  color: #555;
  cursor: not-allowed;
}

.status-msg {
  text-align: center;
  font-size: 0.9rem;
  color: #00d4ff;
  padding: 20px 0;
}

.status-msg.empty {
  color: #777;
}

.pulse {
  animation: pulse-anim 1s infinite;
}

@keyframes pulse-anim {
  0% { opacity: 0.2; }
  50% { opacity: 1; }
  100% { opacity: 0.2; }
}

.summary-info {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: #888;
  margin-bottom: 8px;
}

.scroll-area {
  max-height: 150px;
  overflow-y: auto;
  border: 1px solid rgba(255, 255, 255, 0.05);
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}

.patterns-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
  text-align: left;
}

.patterns-table th, .patterns-table td {
  padding: 6px 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.patterns-table th {
  color: #00d4ff;
  font-weight: 600;
  background: rgba(0, 212, 255, 0.05);
}

.pattern-row:hover {
  background: rgba(255, 255, 255, 0.02);
}

.pat-id {
  font-family: monospace;
  color: #a8ffb8;
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pat-regime {
  color: #eee;
}

.pat-count {
  color: #888;
}
</style>

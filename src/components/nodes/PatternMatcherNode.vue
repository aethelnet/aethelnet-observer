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

      <div class="custom-pattern-section" :class="{ 'glitch-alert': alertActive }">
        <div class="pattern-input-group">
          <input 
            v-model="customPattern" 
            placeholder="Regex or text pattern..." 
            class="sci-input"
            @keydown.enter="triggerMatch"
          />
          <button @click="triggerMatch" class="action-btn small">
            MATCH
          </button>
        </div>
        <div v-if="alertActive" class="alert-msg">
          ⚠️ PATTERN TRIGGERED! MATCHES: {{ alertMatches }} ⚠️
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'

const props = defineProps<{
  node: any
  globalNodes?: any[]
  globalLinks?: any[]
}>()

const patterns = ref<any[]>([])
const loading = ref(true)
const isUpdating = ref(false)
const lastAnalysis = ref<string | null>(null)

const customPattern = ref('')
const alertActive = ref(false)
const alertMatches = ref(0)
let alertTimeout: any = null

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
      // Assume backend handles it or we use WebSockets later
      await fetchPatterns()
      isUpdating.value = false
    } else {
      isUpdating.value = false
    }
  } catch (e) {
    console.error("Failed to trigger patterns update:", e)
    isUpdating.value = false
  }
}

async function triggerMatch() {
  if (!customPattern.value) return
  try {
    const url = API_BASE ? `${API_BASE}/lgnn/pattern/match` : `/api/lgnn/pattern/match`
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pattern: customPattern.value,
        target_node_id: props.node.id,
        regex_mode: true
      })
    })
  } catch (e) {
    console.error("Pattern match failed", e)
  }
}

function handleGlobalEvent(e: Event) {
  const customEvent = e as CustomEvent
  if (customEvent.detail?.event === 'pattern_alert') {
    const payload = customEvent.detail.payload
    if (payload && payload.target_node_id === props.node.id) {
      alertActive.value = true
      alertMatches.value = payload.matches
      if (alertTimeout) clearTimeout(alertTimeout)
      alertTimeout = setTimeout(() => {
        alertActive.value = false
      }, 3000)
    }
  }
}

onMounted(() => {
  fetchPatterns()
  window.addEventListener('aethel-global-event', handleGlobalEvent)
})

onUnmounted(() => {
  window.removeEventListener('aethel-global-event', handleGlobalEvent)
  if (alertTimeout) clearTimeout(alertTimeout)
})
</script>

<style scoped>
.pattern-matcher-node {
  width: 320px;
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(236, 72, 153, 0.3);
  border-radius: 16px;
  color: #fff;
  font-family: 'Space Mono', monospace;
  overflow: hidden;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6), inset 0 0 20px rgba(236, 72, 153, 0.05);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.header {
  background: linear-gradient(90deg, rgba(236, 72, 153, 0.2) 0%, transparent 100%);
  padding: 12px;
  display: flex;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.icon {
  font-size: 1.2rem;
  margin-right: 8px;
}

.title {
  font-weight: 700;
  letter-spacing: 1px;
  color: #f8fafc;
  flex-grow: 1;
  font-size: 13px;
}

.badge {
  font-size: 0.7rem;
  background: #ec4899;
  color: #fff;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 900;
  box-shadow: 0 0 10px #ec4899;
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
  background: linear-gradient(135deg, rgba(236, 72, 153, 0.2), rgba(190, 24, 93, 0.1));
  border: 1px solid rgba(236, 72, 153, 0.5);
  color: #fbcfe8;
  padding: 12px;
  border-radius: 8px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s;
  font-family: 'Space Mono', monospace;
  text-transform: uppercase;
  letter-spacing: 1.5px;
}

.action-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(236, 72, 153, 0.3), rgba(190, 24, 93, 0.2));
  color: #fff;
  box-shadow: 0 0 20px rgba(236, 72, 153, 0.3);
  transform: translateY(-2px);
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
  color: #ec4899;
  font-weight: 600;
  background: rgba(236, 72, 153, 0.05);
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

.custom-pattern-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed rgba(236, 72, 153, 0.3);
  transition: all 0.3s;
}

.pattern-input-group {
  display: flex;
  gap: 8px;
}

.sci-input {
  flex: 1;
  background: rgba(0,0,0,0.25);
  border: 1px solid rgba(236, 72, 153, 0.3);
  border-radius: 8px;
  color: #e2e8f0;
  padding: 10px;
  font-family: 'Space Mono', monospace;
  font-size: 12px;
  outline: none;
  transition: border-color 0.3s;
}
.sci-input:focus {
  border-color: #f472b6;
}

.action-btn.small {
  width: auto;
  padding: 6px 12px;
}

.alert-msg {
  margin-top: 8px;
  color: #E03C31;
  font-weight: 900;
  text-align: center;
  font-size: 10px;
  letter-spacing: 1px;
  text-shadow: 0 0 5px rgba(224, 60, 49, 0.8);
  animation: blink 0.5s infinite;
}

.glitch-alert {
  box-shadow: 0 0 15px rgba(224, 60, 49, 0.5);
  border-color: #E03C31;
  animation: glitch 0.2s infinite;
}

@keyframes glitch {
  0% { transform: translate(1px, 1px); }
  25% { transform: translate(-1px, -1px); }
  50% { transform: translate(1px, -1px); }
  75% { transform: translate(-1px, 1px); }
  100% { transform: translate(1px, 1px); }
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
</style>

<template>
  <div class="forge-market-view">
    <div class="market-header">
      <div class="header-content">
        <h1>FORGE MARKET</h1>
        <p class="subtitle">// UNIT 734 APP ECOSYSTEM</p>
      </div>
      <div class="system-status">
        <span class="status-indicator"></span>
        <span class="status-indicator"></span>
        <span>CORE SYNCED</span>
      </div>
      <button class="brutal-btn" @click="showWorkbench = true" style="margin-left: 20px;">
        [ + CREATE COMMUNITY APP ]
      </button>
    </div>

    <div class="apps-grid">
      <div v-for="app in apps" :key="app.id" class="brutal-card">
        <div class="card-header">
          <span class="app-icon">{{ app.icon }}</span>
          <h3 class="app-name">{{ app.name }}</h3>
        </div>
        <p class="app-desc">{{ app.description }}</p>
        
        <div class="card-actions">
          <button v-if="app.status === 'uninstalled'" class="brutal-btn primary" @click="installApp(app)">
            [ INSTALL ]
          </button>
          
          <button v-else-if="app.status === 'installing'" class="brutal-btn installing" disabled>
            [ {{ app.progress }}% ]
          </button>
          
          <button v-else-if="app.status === 'installed'" class="brutal-btn" @click="launchApp(app)">
            [ LAUNCH ]
          </button>
          
          <button v-if="app.status === 'installed'" class="brutal-btn remove" @click="removeApp(app)" title="Uninstall">
            X
          </button>
        </div>
      </div>
    </div>

    <!-- Active App Overlay -->
    <div v-if="activeApp" class="app-overlay" @click.self="closeApp">
      <div class="app-window">
        <div class="app-header">
          <div class="app-title">
            <span class="app-icon">{{ activeApp.icon }}</span>
            {{ activeApp.name }}
          </div>
          <button class="close-btn" @click="closeApp">X</button>
        </div>
        <div class="app-content">
          <!-- INITIALIZATION PHASE -->
          <div v-if="appState === 'initializing'" class="placeholder-content">
            <h2>INITIALIZING...</h2>
            <p>[SYS] Execution environment mounted.</p>
            <p>[SYS] Binding to LGNN Core...</p>
            <p class="blink">_</p>
          </div>

          <!-- OMNI DECODER LOGIC -->
          <div v-else-if="appState === 'running' && activeApp.id === 'app1'" class="running-app code-stream">
            <h3>[ DECRYPTING INCOMING PACKETS ]</h3>
            <div class="stream-line" v-for="(line, idx) in appLogs" :key="idx">
              > {{ line }}
            </div>
            <p class="blink">_</p>
          </div>

          <!-- LGNN P2P BRIDGE -->
          <div v-else-if="appState === 'running' && activeApp.id === 'app2'" class="running-app code-stream">
            <h3>[ MESH NETWORK TOPOLOGY ]</h3>
            <div class="stream-line" v-for="(line, idx) in appLogs" :key="idx">
              > {{ line }}
            </div>
            <button class="brutal-btn small mt-4" @click="fetchPeers">[ REFRESH PEERS ]</button>
          </div>

          <!-- Z-SCORE SNIPER LOGIC -->
          <div v-else-if="appState === 'running' && activeApp.id === 'app3'" class="running-app code-stream">
            <h3>[ Z-SCORE ANOMALY RADAR ]</h3>
            <div v-if="appLogs.length === 0" class="stream-line">> SCANNING NEURAL MANIFOLD...</div>
            <div class="stream-line text-red" v-for="(line, idx) in appLogs" :key="idx">
              > {{ line }}
            </div>
            <button class="brutal-btn small mt-4" @click="snipeAnomalies">[ SWEEP GRAPH ]</button>
          </div>

          <!-- SWARM ORCHESTRATOR LOGIC -->
          <div v-else-if="appState === 'running' && activeApp.id === 'app4'" class="running-app">
            <h3>[ SWARM CONTROL LINK ACTIVE ]</h3>
            <div class="agent-list">
              <div class="agent-row" v-for="i in 4" :key="i">
                <span>AGENT_0{{ i }}</span>
                <span class="status text-green">SYNCHRONIZED</span>
                <span>CPU: {{ Math.floor(Math.random() * 40 + 10) }}%</span>
              </div>
            </div>
          </div>

          <!-- GENERIC RUNNING PHASE -->
          <div v-else-if="appState === 'running'" class="running-app">
            <h3>[ SUB-SYSTEM ONLINE ]</h3>
            <p>Accessing Core DB...</p>
            <p>Module {{ activeApp.name }} successfully bound to Aethelnet.</p>
            <p>Awaiting user commands...</p>
            <p class="blink">_</p>
          </div>
        </div>
      </div>
    </div>
    
    <!-- The Node Builder (Workbench) -->
    <WorkbenchView v-if="showWorkbench" @close="showWorkbench = false" @save="onSaveBlueprint" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import WorkbenchView from './WorkbenchView.vue'
import { API_BASE } from '../shared/api.js'

const showWorkbench = ref(false)

const defaultApps = [
  { id: 'app1', name: 'OMNI DECODER', description: 'Decrypt and analyze raw data streams.', icon: '👁️', status: 'installed', progress: 0 },
  { id: 'app2', name: 'PEER MAP', description: 'Visualize and connect to P2P nodes.', icon: '🌐', status: 'uninstalled', progress: 0 },
  { id: 'app3', name: 'Z-SCORE SNIPER', description: 'Scan the neural manifold for trading Z-Score anomalies.', icon: '🎯', status: 'installed', progress: 0 },
  { id: 'app4', name: 'SWARM ORCHESTRATOR', description: 'Coordinate multi-agent behaviors.', icon: '🐝', status: 'uninstalled', progress: 0 },
  { id: 'app5', name: 'CONTEXT MEMORY', description: 'View and edit long-term context graphs.', icon: '🧠', status: 'uninstalled', progress: 0 },
  { id: 'app6', name: 'SIGNAL FILTER', description: 'Advanced DSP filtering for noisy streams.', icon: '🎛️', status: 'uninstalled', progress: 0 }
]

const apps = ref<any[]>([])

onMounted(() => {
  const saved = localStorage.getItem('forge_apps_v2')
  if (saved) {
    apps.value = JSON.parse(saved)
  } else {
    apps.value = [...defaultApps]
  }
})

watch(apps, (newVal) => {
  localStorage.setItem('forge_apps_v2', JSON.stringify(newVal))
}, { deep: true })

const activeApp = ref<any>(null)
const appState = ref('initializing')
const appLogs = ref<string[]>([])
let streamInterval: any = null

const installApp = (app: any) => {
  app.status = 'installing'
  app.progress = 0
  
  const interval = setInterval(() => {
    app.progress += Math.floor(Math.random() * 20) + 10
    if (app.progress >= 100) {
      app.progress = 100
      app.status = 'installed'
      clearInterval(interval)
    }
  }, 200)
}

const removeApp = (app: any) => {
  app.status = 'uninstalled'
  app.progress = 0
}

const launchApp = (app: any) => {
  activeApp.value = app
  appState.value = 'initializing'
  appLogs.value = []
  
  setTimeout(() => {
    appState.value = 'running'
    if (app.id === 'app1') {
      startOmniDecoder()
    } else if (app.id === 'app2') {
      fetchPeers()
    } else if (app.id === 'app3') {
      snipeAnomalies()
    }
  }, 1500)
}

const fetchPeers = async () => {
  appLogs.value = ['> Querying Global Tracker...']
  try {
    const res = await fetch(`${API_BASE}/p2p/tracker/peers`)
    const data = await res.json()
    if (data.peers && data.peers.length > 0) {
      appLogs.value = data.peers.map((p: string) => `[PEER] ${p}`)
    } else {
      appLogs.value = ['[SYS] No peers active.']
    }
  } catch (e: any) {
    appLogs.value = [`[ERR] ${e.message}`]
  }
}

const snipeAnomalies = async () => {
  appLogs.value = ['> Scanning Prophit Engine for Z-Score Trading Anomalies...']
  try {
    const res = await fetch(`${API_BASE || '/api'}/trading/preview?symbol=BTCUSDT`)
    const data = await res.json()
    // Extracting actual trading previews from the Sovereign Engine
    const anomalies = (data.previews || []).filter((p: any) => Math.abs(p.z_score) > 1.5)
    if (anomalies.length > 0) {
      appLogs.value = anomalies.map((p: any) => `[TRADE SIGNAL] ${p.symbol} | Z-Score: ${p.z_score.toFixed(2)}σ | Action: ${p.side} @ $${p.entry_price}`)
    } else {
      appLogs.value = ['[SYS] No extreme Z-Scores found. Market stable.']
    }
  } catch (e: any) {
    appLogs.value = [`[ERR] ${e.message}`]
  }
}

const startOmniDecoder = () => {
  const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*'
  streamInterval = setInterval(() => {
    let line = ''
    for (let i = 0; i < 40; i++) {
      line += characters.charAt(Math.floor(Math.random() * characters.length))
    }
    appLogs.value.push(`0x${Math.floor(Math.random()*10000).toString(16)}: ${line}`)
    if (appLogs.value.length > 15) {
      appLogs.value.shift()
    }
  }, 100)
}

const closeApp = () => {
  activeApp.value = null
  if (streamInterval) clearInterval(streamInterval)
}

const onSaveBlueprint = (blueprint: any) => {
  apps.value.push({
    id: blueprint.id,
    name: blueprint.name,
    description: `Community App created by you. Output mode: ${blueprint.outputType}`,
    icon: '🧩',
    status: 'installed',
    progress: 100
  })
  showWorkbench.value = false
}
</script>

<style scoped>
/* Previous styles remain exactly the same */
.forge-market-view {
  padding: 40px;
  height: 100vh;
  box-sizing: border-box;
  background: #ffffff;
  color: #000000;
  overflow-y: auto;
  font-family: 'Space Mono', monospace;
}

.market-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 40px;
  border-bottom: 4px solid #000000;
  padding-bottom: 20px;
}

.header-content h1 {
  margin: 0;
  font-size: 32px;
  font-weight: 900;
  letter-spacing: -1px;
}

.subtitle {
  margin: 5px 0 0 0;
  font-weight: bold;
  color: #666666;
  text-transform: uppercase;
}

.system-status {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: bold;
  font-size: 14px;
  border: 2px solid #000000;
  padding: 5px 15px;
}

.status-indicator {
  width: 10px;
  height: 10px;
  background: #000000;
}

.apps-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 30px;
}

.brutal-card {
  border: 4px solid #000000;
  padding: 20px;
  background: #f4f4f4;
  box-shadow: 8px 8px 0px #000000;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: transform 0.1s, box-shadow 0.1s;
}

.brutal-card:hover {
  transform: translate(-2px, -2px);
  box-shadow: 10px 10px 0px #000000;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
}

.app-icon {
  font-size: 32px;
}

.app-name {
  margin: 0;
  font-size: 20px;
  font-weight: 900;
  text-transform: uppercase;
}

.app-desc {
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 20px;
  flex-grow: 1;
}

.card-actions {
  display: flex;
  gap: 10px;
}

.brutal-btn {
  background: #ffffff;
  color: #000000;
  border: 2px solid #000000;
  padding: 10px 15px;
  font-family: 'Space Mono', monospace;
  font-size: 14px;
  font-weight: bold;
  cursor: pointer;
  text-transform: uppercase;
  flex-grow: 1;
}

.brutal-btn.primary {
  background: #000000;
  color: #ffffff;
}

.brutal-btn.primary:hover {
  background: #ffffff;
  color: #000000;
}

.brutal-btn:hover:not(:disabled) {
  background: #000000;
  color: #ffffff;
}

.brutal-btn.installing {
  background: #cccccc;
  cursor: not-allowed;
}

.brutal-btn.remove {
  flex-grow: 0;
  padding: 10px 15px;
  background: #ffffff;
  color: #cc0000;
  border-color: #cc0000;
}
.brutal-btn.remove:hover {
  background: #cc0000;
  color: #ffffff;
}

/* Overlay Styles */
.app-overlay {
  position: fixed;
  inset: 0;
  background: rgba(255, 255, 255, 0.9);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.app-window {
  width: 100%;
  max-width: 800px;
  height: 600px;
  background: #ffffff;
  border: 4px solid #000000;
  box-shadow: 16px 16px 0px #000000;
  display: flex;
  flex-direction: column;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 4px solid #000000;
  background: #f4f4f4;
}

.app-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 900;
  font-size: 20px;
}

.close-btn {
  background: #ffffff;
  border: 4px solid #000000;
  color: #000000;
  font-size: 20px;
  font-weight: 900;
  width: 40px;
  height: 40px;
  cursor: pointer;
}

.close-btn:hover {
  background: #000000;
  color: #ffffff;
}

.app-content {
  flex: 1;
  padding: 40px;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  background: #FFFFFF;
  color: #111111;
  overflow: hidden;
  border-top: 4px solid #111111;
  background-image: linear-gradient(rgba(17, 17, 17, 0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(17, 17, 17, 0.05) 1px, transparent 1px);
  background-size: 20px 20px;
}

.placeholder-content, .running-app {
  text-align: left;
  width: 100%;
}

.placeholder-content h2, .running-app h3 {
  font-size: 24px;
  margin-bottom: 20px;
  font-weight: 900;
  text-transform: uppercase;
}

.placeholder-content p, .running-app p {
  font-size: 16px;
  margin: 10px 0;
  font-weight: bold;
}

/* App Specific Styles */
.code-stream {
  font-size: 12px;
  line-height: 1.2;
}

.stream-line {
  color: #555555;
  font-weight: bold;
}

.grid-radar {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 2px;
  margin-top: 20px;
  border: 4px solid #111111;
  background: #111111;
}

.radar-cell {
  background: #FFFFFF;
  padding: 10px;
  text-align: center;
  font-size: 12px;
  font-weight: bold;
  color: #111111;
}

.radar-cell.anomaly {
  background: #FF3366;
  color: #FFFFFF;
}

.agent-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 20px;
}

.agent-row {
  display: flex;
  justify-content: space-between;
  padding: 10px;
  border: 4px solid #111111;
  background: #F8F8F8;
  font-weight: bold;
}

.text-green { color: #32D74B; }
.text-red { color: #FF3366; }

.blink {
  animation: blink 1s step-end infinite;
}

@keyframes blink {
  50% { opacity: 0; }
}
</style>

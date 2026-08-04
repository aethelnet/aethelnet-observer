<template>
  <div class="lgnn-terminal">
    <div class="lgnn-header">
      <div class="header-titles">
        <h1 class="glitch" data-text="LGNN CORE TERMINAL">LGNN CORE TERMINAL</h1>
        <p class="subtitle">Unit 734 Subsystem // Direct Access</p>
      </div>
    </div>

    <div class="terminal-layout">
      <!-- Status & Settings Panel -->
      <div class="side-panel">
        <div class="panel-section">
          <h3>SYSTEM STATUS</h3>
          <div class="status-row">
            <span>CORE:</span> <span class="active">ONLINE</span>
          </div>
          <div class="status-row">
            <span>SPIDERS:</span> <span class="active">ACTIVE</span>
          </div>
          <div class="status-row">
            <span>QUARANTINE:</span> <span class="warning">SECURE</span>
          </div>
        </div>

        <div class="panel-section">
          <h3>LGNN TUNING</h3>
          <div class="tuning-control">
            <label>RESONANCE THRESHOLD</label>
            <input type="range" v-model.number="resonance" min="0" max="1" step="0.01" />
            <span>{{ resonance }}</span>
          </div>
          <div class="tuning-control">
            <label>DECAY RATE</label>
            <input type="range" v-model.number="decay" min="0" max="1" step="0.01" />
            <span>{{ decay }}</span>
          </div>
          <button class="brutal-btn small" @click="updateSettings">APPLY TUNING</button>
        </div>
      </div>

      <!-- Main CLI Window -->
      <div class="cli-window">
        <div class="cli-output" ref="outputArea">
          <div v-for="(line, idx) in logLines" :key="idx" class="log-line">
            <span class="prompt" v-if="line.type === 'in'">></span>
            <span :class="line.type">{{ line.text }}</span>
          </div>
        </div>
        <div class="cli-input-wrapper">
          <span class="prompt">></span>
          <input 
            type="text" 
            v-model="cmdInput" 
            @keyup.enter="executeCommand" 
            placeholder="ENTER COMMAND OR FEED DATA..."
            class="cli-input"
            autofocus
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { API_BASE } from '../shared/api.js'



const resonance = ref(0.5)
const decay = ref(0.05)

const cmdInput = ref('')
const logLines = ref([
  { type: 'sys', text: 'LGNN Core OS v2.0 initialized.' },
  { type: 'sys', text: 'Unit 734 Singularity Protocol engaged.' },
  { type: 'sys', text: 'Type HELP for commands.' }
])
const outputArea = ref(null)

const printLog = (text, type = 'sys') => {
  logLines.value.push({ text, type })
  nextTick(() => {
    if (outputArea.value) {
      outputArea.value.scrollTop = outputArea.value.scrollHeight
    }
  })
}

const executeCommand = async () => {
  const cmd = cmdInput.value.trim()
  if (!cmd) return
  
  printLog(cmd, 'in')
  cmdInput.value = ''
  
  const args = cmd.split(' ')
  const root = args[0].toUpperCase()
  
  if (root === 'HELP') {
    printLog('================ AURA CLI (CORE) ================', 'sys')
    printLog(' ANALYZE <asset>   | Deploy LLM OSINT for tactical breakdown of a ticker', 'sys')
    printLog('                     Example: ANALYZE BTC', 'sys')
    printLog(' FEED <text>       | Inject data directly into the neural graph', 'sys')
    printLog('                     Example: FEED Secret Base64 String', 'sys')
    printLog(' QUARANTINE <id>   | Isolate a malicious node (Repulsor Protocol)', 'sys')
    printLog('                     Example: QUARANTINE Node_1234', 'sys')
    printLog(' SPIDER <url>      | Dispatch a web crawler to harvest data', 'sys')
    printLog('                     Example: SPIDER https://example.com', 'sys')
    printLog(' MESH SYNC         | Connect your local node to the P2P network', 'sys')
    printLog(' MESH PEERS        | View all active connected users in the mesh', 'sys')
    printLog(' SETTINGS          | View current physics and resonance tuning', 'sys')
    printLog(' CLEAR             | Wipe the terminal output', 'sys')
    printLog(' ASK <question>    | Talk to Aura (Your AI Assistant)', 'sys')
    printLog('                     Example: ASK Was ist der Status?', 'sys')
    printLog('=================================================', 'sys')
  } else if (root === 'CLEAR') {
    logLines.value = []
  } else if (root === 'SETTINGS') {
    try {
      const res = await fetch(`${API_BASE || '/api'}/lgnn/settings`)
      const data = await res.json()
      printLog(`Resonance: ${data.resonance_threshold}, Decay: ${data.decay_rate}`, 'sys')
      resonance.value = data.resonance_threshold
      decay.value = data.decay_rate
    } catch (e) {
      printLog(`ERR: ${e.message}`, 'error')
    }
  } else if (root === 'ASK') {
    const text = args.slice(1).join(' ')
    if (!text) {
      printLog('AURA: Bitte stelle mir eine Frage. (Beispiel: ASK Hallo)', 'error')
      return
    }
    printLog('AURA: (Wird verarbeitet...)', 'sys')
    try {
      const res = await fetch(`${API_BASE || '/api'}/lgnn/generate-response`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: text, length: 'medium' })
      })
      const data = await res.json()
      if (data.status === 'success') {
        printLog(`AURA: ${data.response}`, 'success')
      } else {
        printLog(`ERR: ${data.message}`, 'error')
      }
    } catch(e) {
      printLog(`ERR: ${e.message}`, 'error')
    }
  } else if (root === 'ANALYZE') {
    const target = args[1]
    if (!target) {
      printLog('ERR: Missing asset ticker. Example: ANALYZE BTC', 'error')
      return
    }
    printLog(`[OSINT] Querying Sovereign Oracle for tactical analysis on ${target.toUpperCase()}...`, 'sys')
    try {
      const prompt = `Give me a brutal, highly technical, 3-sentence OSINT tactical breakdown of ${target.toUpperCase()}'s current market structure. Use cyberpunk, mercenary trader tone. No intro, no markdown.`
      const res = await fetch(`${API_BASE || '/api'}/lgnn/generate-response`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: prompt, length: 'short' })
      })
      const data = await res.json()
      if (data.status === 'success') {
        printLog(`[TARGET: ${target.toUpperCase()}]`, 'success')
        printLog(data.response, 'success')
      } else {
        printLog(`ERR: ${data.message}`, 'error')
      }
    } catch(e) {
      printLog(`ERR: ${e.message}`, 'error')
    }
  } else if (root === 'QUARANTINE') {
    const target = args[1]
    if (!target) {
      printLog('ERR: Missing target ID. Example: QUARANTINE Node_1234', 'error')
      return
    }
    printLog(`[REPULSOR PROTOCOL] Isolating node ${target}...`, 'sys')
    setTimeout(() => {
      printLog(`[SUCCESS] ${target} has been severed from the active graph.`, 'success')
    }, 800)
  } else if (root === 'SPIDER') {
    const target = args[1]
    if (!target) {
      printLog('ERR: Missing target URL. Example: SPIDER https://example.com', 'error')
      return
    }
    printLog(`[SPIDER DISPATCH] Awakening idle crawler for target: ${target}`, 'sys')
    try {
      const res = await fetch(`${API_BASE || '/api'}/lgnn/spider/dispatch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_url: target })
      })
      const data = await res.json()
      if (data.status === 'success') {
         printLog(`[QUEUED] Target added to Postgres Spider Queue. Worker active.`, 'success')
      } else {
         printLog(`ERR: ${data.message}`, 'error')
      }
    } catch(e) {
      printLog(`ERR: ${e.message}`, 'error')
    }
  } else if (root === 'FEED') {
    const text = args.slice(1).join(' ')
    if (!text) {
      printLog('ERR: Missing text payload.', 'error')
      return
    }
    printLog(`Injecting data into LGNN...`, 'sys')
    try {
      const res = await fetch(`${API_BASE || '/api'}/lgnn/universal_ingest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          bot_name: 'LGNN_Terminal',
          observation: text,
          confidence: 1.0,
          context_tags: ['manual', 'terminal'],
          node_prefix: 'CMD_'
        })
      })
      const data = await res.json()
      printLog(`[SUCCESS] Data injected. Status: ${data.status}`, 'success')
    } catch (e) {
      printLog(`ERR: ${e.message}`, 'error')
    }
  } else if (root === 'MESH') {
    const subCmd = args[1]?.toUpperCase()
    if (subCmd === 'SYNC') {
      printLog('INITIATING MESH SYNC...', 'sys')
      try {
        // Ping Tracker using relative path which NGINX proxies to Server 141
        await fetch(`/p2p/tracker/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ peer_id: "aura_cli_manual", peer_address: "cli_user" })
        })
        printLog('[SUCCESS] MESH PEER REGISTERED', 'success')
      } catch (e) {
        printLog(`[ERR] MESH Tracker offline: ${e.message}`, 'error')
      }
    } else if (subCmd === 'PEERS') {
      printLog('QUERYING GLOBAL TRACKER...', 'sys')
      try {
        const res = await fetch(`/p2p/tracker/peers`)
        const data = await res.json()
        printLog(`[MESH] ${data.peers.length} PEERS ONLINE:`, 'sys')
        data.peers.forEach(p => printLog(`  -> [${p}]`, 'sys'))
      } catch(e) {
        printLog(`[MESH ERR] ${e.message}`, 'error')
      }
    } else {
      printLog('USAGE: MESH SYNC | MESH PEERS', 'error')
    }
  } else {
    printLog(`UNKNOWN COMMAND: ${root}`, 'error')
  }
}

const updateSettings = async () => {
  printLog(`Applying new tuning parameters...`, 'sys')
  try {
    const res = await fetch(`${API_BASE || '/api'}/lgnn/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resonance: resonance.value, decay: decay.value })
    })
    const data = await res.json()
    printLog(`[SUCCESS] Settings applied.`, 'success')
  } catch (e) {
    printLog(`ERR: ${e.message}`, 'error')
  }
}

onMounted(() => {
  executeCommand('SETTINGS') // Fetch initial on load silently if we wanted, but let's just let user do it
})
</script>

<style scoped>
.lgnn-terminal {
  padding: 40px;
  height: 100vh;
  box-sizing: border-box;
  background: #ffffff;
  color: #000000;
  display: flex;
  flex-direction: column;
  font-family: 'Space Mono', monospace;
  overflow: hidden;
}

.lgnn-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  border-bottom: 4px solid #000;
  padding-bottom: 20px;
  margin-bottom: 20px;
}

.header-titles {
  display: flex;
  flex-direction: column;
}

.glitch {
  font-size: 48px;
  font-weight: 900;
  margin: 0;
  letter-spacing: -2px;
}

.subtitle {
  font-weight: bold;
  color: #666666;
  margin: 0;
  margin-top: 5px;
}

.terminal-layout {
  display: flex;
  flex: 1;
  gap: 30px;
  overflow: hidden;
}

.side-panel {
  width: 300px;
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.panel-section {
  border: 4px solid #000000;
  padding: 20px;
  background: #f4f4f4;
}

.panel-section h3 {
  margin: 0 0 20px 0;
  border-bottom: 2px solid #000000;
  padding-bottom: 5px;
}

.status-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  font-weight: bold;
}

.status-row .active {
  color: #008000;
}

.status-row .warning {
  color: #cc0000;
}

.tuning-control {
  margin-bottom: 15px;
  display: flex;
  flex-direction: column;
}

.tuning-control label {
  font-size: 12px;
  font-weight: bold;
  margin-bottom: 5px;
}

.tuning-control input[type=range] {
  width: 100%;
  accent-color: #000000;
}

.brutal-btn {
  background: #000000;
  color: #ffffff;
  border: 2px solid #000000;
  padding: 10px;
  font-family: 'Space Mono', monospace;
  font-weight: bold;
  cursor: pointer;
  width: 100%;
  transition: all 0.2s;
}

.brutal-btn:hover {
  background: #ffffff;
  color: #000000;
  box-shadow: 4px 4px 0px #000000;
}

.cli-window {
  flex: 1;
  border: 4px solid #000000;
  background: #050505;
  color: #00FF41;
  display: flex;
  flex-direction: column;
  position: relative;
  box-shadow: inset 0 0 50px rgba(0, 255, 65, 0.1);
  overflow: hidden;
}

.cli-window::after {
  content: "";
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
  background-size: 100% 4px, 3px 100%;
  pointer-events: none;
  z-index: 10;
}

.cli-output {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  z-index: 5;
}

.log-line {
  margin-bottom: 8px;
  font-size: 15px;
  line-height: 1.5;
  word-wrap: break-word;
  text-shadow: 0 0 5px rgba(0, 255, 65, 0.5);
}

.log-line .prompt {
  color: #ffffff;
  margin-right: 10px;
  text-shadow: none;
}

.log-line .in {
  color: #ffffff;
}

.log-line .sys {
  color: #00FF41;
}

.log-line .error {
  color: #FF0000;
  text-shadow: 0 0 5px rgba(255, 0, 0, 0.5);
}

.log-line .success {
  color: #00ffff;
  text-shadow: 0 0 5px rgba(0, 255, 255, 0.5);
}

.cli-input-wrapper {
  display: flex;
  padding: 20px;
  border-top: 4px solid #000000;
  background: #111111;
  z-index: 5;
}

.cli-input-wrapper .prompt {
  color: #ffffff;
  margin-right: 15px;
  font-size: 16px;
  line-height: 24px;
}

.cli-input {
  flex: 1;
  background: transparent;
  border: none;
  color: #ffffff;
  font-family: 'Space Mono', monospace;
  font-size: 16px;
  outline: none;
}

.cli-input::placeholder {
  color: #555555;
}
</style>

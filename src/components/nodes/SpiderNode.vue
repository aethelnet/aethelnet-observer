<template>
  <div class="spider-node glass-panel">
    <div class="header">
      <span class="icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width:14px; height:14px;">
          <circle cx="12" cy="12" r="3" />
          <path d="M12 8 L12 3 M12 16 L12 21 M8 12 L3 12 M16 12 L21 12" />
          <path d="M9 9 L5 5 M15 15 L19 19 M9 15 L5 19 M15 9 L19 5" />
          <circle cx="12" cy="3" r="1" fill="currentColor"/>
          <circle cx="12" cy="21" r="1" fill="currentColor"/>
          <circle cx="3" cy="12" r="1" fill="currentColor"/>
          <circle cx="21" cy="12" r="1" fill="currentColor"/>
          <circle cx="5" cy="5" r="1" fill="currentColor"/>
          <circle cx="19" cy="19" r="1" fill="currentColor"/>
          <circle cx="5" cy="19" r="1" fill="currentColor"/>
          <circle cx="19" cy="5" r="1" fill="currentColor"/>
        </svg>
      </span>
      <span class="title">SPIDER PROTOCOL</span>
      <button class="header-btn" @click="query = ''">🔄</button>
    </div>
    
    <div class="spider-input-group">
      <input 
        v-model="query" 
        placeholder="Enter Target URL or Query..." 
        class="sci-input"
        @keydown.enter="startCrawl"
        :disabled="isCrawling"
      />
      <button @click="startCrawl" class="spider-btn" :disabled="isCrawling">
        <span class="btn-glitch" v-if="isCrawling"></span>
        {{ isCrawling ? 'SCANNING...' : 'INJECT' }}
      </button>
    </div>

    <!-- Crawl Depth Slider -->
    <div class="depth-control">
      <div class="depth-labels">
        <span class="depth-title">PENETRATION DEPTH [ {{ depth }} ]</span>
        <span class="depth-max">MAX: 5</span>
      </div>
      <input 
        type="range" 
        min="1" 
        max="5" 
        step="1" 
        v-model.number="depth" 
        class="sci-range"
        :disabled="isCrawling"
      />
    </div>

    <div v-if="isCrawling" class="spider-status">
      <div class="loader-container">
        <div class="loader-bar" :style="{ width: crawlProgress + '%' }"></div>
      </div>
      <div class="status-text">
        <span>Extracting Tokens: <span class="highlight">{{ domNodes }}</span></span>
        <span class="blink">Bypassing...</span>
      </div>
    </div>

    <div class="spider-results-terminal glass-panel" v-if="results.length > 0 || isCrawling" ref="terminalRef">
      <div class="terminal-header">
        <span class="terminal-dot red"></span>
        <span class="terminal-dot yellow"></span>
        <span class="terminal-dot green"></span>
        <span class="terminal-title">DATA STREAM</span>
      </div>
      <div class="terminal-body">
        <div v-for="(res, idx) in results" :key="idx" class="terminal-line">
          <span class="prompt-arrow">>$</span> <span class="res-text">{{ res }}</span>
        </div>
        <div v-if="isCrawling" class="terminal-line blink-cursor">
          <span class="prompt-arrow">>$</span> <span class="res-text scanning-text">_</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps<{
  node: any
}>()

const emit = defineEmits(['refresh', 'toggle-expand'])

const query = ref('')
const depth = ref(1)
const isCrawling = ref(false)
const domNodes = ref(0)
const crawlProgress = ref(0)
const results = ref<string[]>([])
const terminalRef = ref<HTMLElement | null>(null)

let interval: any

async function startCrawl() {
  if (!query.value || isCrawling.value) return
  
  isCrawling.value = true
  results.value = []
  domNodes.value = 0
  
  // Fake animation for the UI

  interval = setInterval(() => {
    domNodes.value += Math.floor(Math.random() * 40)
    if (crawlProgress.value < 90) crawlProgress.value += Math.random() * 5
    scrollToBottom()
  }, 200)

  try {
    const API_BASE = (window as any).API_BASE || ''
    const url = API_BASE ? `${API_BASE}/lgnn/spider/crawl` : '/api/lgnn/spider/crawl'
    
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url: query.value,
        parent_id: props.node.parent_id || 'ROOT',
        spider_node_id: props.node.id,
        depth: depth.value
      })
    })
    
    const data = await res.json()
    
    if (data.status === 'success') {
        // If results were already streamed, don't overwrite them
        if (results.value.length === 0) {
            results.value = data.results
        }
        domNodes.value = data.dom_nodes
        emit('refresh')
    } else {
        results.value = [`ERROR: ${data.error}`]
    }
  } catch (err: any) {
    results.value = [`FAILED: ${err.message}`]
  } finally {
    clearInterval(interval)
    isCrawling.value = false
  }
}

function handleGlobalEvent(e: Event) {
  const customEvent = e as CustomEvent
  if (customEvent.detail?.event === 'spider_stream') {
    const payload = customEvent.detail.payload
    if (payload && payload.spider_node_id === props.node.id) {
      if (!results.value.includes(payload.content)) {
          results.value.push(payload.content)
          scrollToBottom()
      }
    }
  }
}

function scrollToBottom() {
  setTimeout(() => {
    if (terminalRef.value) {
      const body = terminalRef.value.querySelector('.terminal-body')
      if (body) {
        body.scrollTop = body.scrollHeight
      }
    }
  }, 50)
}

onMounted(() => {
  window.addEventListener('aethel-global-event', handleGlobalEvent)
})

onUnmounted(() => {
  window.removeEventListener('aethel-global-event', handleGlobalEvent)
})
</script>

<style scoped>
.spider-node {
  width: 100%;
  height: 100%;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: var(--color-bg-primary);
  color: var(--color-text-main);
}

.header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  border-bottom: 2px solid var(--border-color);
  padding-bottom: 8px;
}
.header .icon {
  color: var(--color-text-main);
}
.header .title {
  color: var(--color-text-main);
  font-family: var(--font-family);
  font-size: 18px;
  font-weight: bold;
  flex: 1;
}
.header-btn {
  background: #ffffff;
  border: 2px solid #000000;
  box-shadow: 2px 2px 0px #000000;
  cursor: pointer;
  padding: 4px 8px;
  font-weight: bold;
}
.header-btn:hover {
  background: #000000;
  color: #ffffff;
  transform: translate(-2px, -2px);
  box-shadow: 4px 4px 0px #000000;
}

.spider-input-group {
  display: flex;
  gap: 12px;
}

.sci-input {
  flex: 1;
  background: #ffffff;
  border: 2px solid #000000;
  color: #000000;
  padding: 12px;
  font-family: var(--font-family);
  font-size: 14px;
  outline: none;
  border-radius: 0;
}

.sci-input:focus {
  background: #f0f0f0;
  box-shadow: 4px 4px 0px #000000;
}

.spider-btn {
  background: #ffffff;
  border: 2px solid #000000;
  color: #000000;
  font-family: var(--font-family);
  font-size: 14px;
  font-weight: bold;
  padding: 0 24px;
  cursor: pointer;
  box-shadow: 2px 2px 0px #000000;
  border-radius: 0;
}

.spider-btn:hover:not(:disabled) {
  background: #000000;
  color: #ffffff;
  transform: translate(-2px, -2px);
  box-shadow: 4px 4px 0px #000000;
}

.spider-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
}

.depth-control {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-top: 12px;
}

.depth-labels {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  font-weight: bold;
}

.sci-range {
  -webkit-appearance: none;
  width: 100%;
  height: 8px;
  background: #000000;
  border-radius: 0;
  outline: none;
}

.sci-range::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px;
  height: 24px;
  background: #ffffff;
  border: 2px solid #000000;
  cursor: pointer;
}

.spider-status {
  display: flex;
  flex-direction: column;
  gap: 12px;
  font-size: 14px;
  font-family: var(--font-family);
  font-weight: bold;
  padding: 12px;
  border: 2px solid #000000;
}

.loader-container {
  height: 8px;
  width: 100%;
  background: #f0f0f0;
  border: 1px solid #000000;
}

.loader-bar {
  width: 30%;
  height: 100%;
  background: #000000;
  animation: scan 1.5s infinite linear alternate;
}

@keyframes scan {
  0% { transform: translateX(0%); }
  100% { transform: translateX(230%); }
}

.status-text {
  display: flex;
  justify-content: space-between;
}

.spider-results-terminal {
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border: 2px solid #000000;
  flex: 1;
  overflow: hidden;
  box-shadow: 4px 4px 0px #000000;
}

.terminal-header {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #000000;
  color: #ffffff;
  padding: 8px 12px;
  font-weight: bold;
}

.terminal-dot {
  width: 12px;
  height: 12px;
  border: 2px solid #ffffff;
}

.terminal-title {
  margin-left: auto;
  font-size: 12px;
  letter-spacing: 1px;
}

.terminal-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  font-size: 14px;
  font-family: var(--font-family);
  background: #ffffff;
  color: #000000;
}

.terminal-line {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  line-height: 1.5;
}

.prompt-arrow {
  font-weight: bold;
}

.res-text {
  word-break: break-word;
}
</style>

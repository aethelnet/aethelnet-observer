<template>
  <div class="spider-node-container" @mousedown.stop @touchstart.stop>
    <div class="spider-header">
      <div class="header-icon"><i class="fas fa-spider"></i></div>
      <div class="header-title">SPIDER PROTOCOL</div>
      <div class="status-dot" :class="{ active: isCrawling }"></div>
    </div>
    
    <div class="spider-body">
      <div class="spider-input-group">
        <input 
          v-model="query" 
          placeholder="Enter URL or Search Query..." 
          class="sci-input"
          @keydown.enter="startCrawl"
        />
        <button @click="startCrawl" class="spider-btn" :disabled="isCrawling">
          <span class="btn-glitch" v-if="isCrawling"></span>
          {{ isCrawling ? 'SCANNING...' : 'CRAWL' }}
        </button>
      </div>

      <!-- Crawl Depth Slider -->
      <div class="depth-control">
        <div class="depth-labels">
          <span class="depth-title">CRAWL DEPTH [ {{ depth }} ]</span>
          <span class="depth-max">MAX: 5</span>
        </div>
        <input 
          type="range" 
          min="1" 
          max="5" 
          step="1" 
          v-model.number="depth" 
          class="sci-range"
        />
      </div>

      <div v-if="isCrawling" class="spider-status">
        <div class="loader-container">
          <div class="loader-bar"></div>
        </div>
        <div class="status-text">
          <span>Extracting DOM nodes: <span class="highlight">{{ domNodes }}</span></span>
          <span class="blink">Filtering noise...</span>
        </div>
      </div>

      <div v-if="results.length > 0" class="spider-results">
        <div class="results-header">DATA FRAGMENTS ACQUIRED:</div>
        <div class="results-list">
          <div v-for="(res, idx) in results" :key="idx" class="result-item">
            <span class="res-arrow">>></span> {{ res }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  node: any
}>()

const emit = defineEmits(['refresh'])

const query = ref('')
const depth = ref(1)
const isCrawling = ref(false)
const domNodes = ref(0)
const results = ref<string[]>([])

let interval: any

async function startCrawl() {
  if (!query.value || isCrawling.value) return
  
  isCrawling.value = true
  results.value = []
  domNodes.value = 0
  
  // Fake animation for the UI
  interval = setInterval(() => {
    domNodes.value += Math.floor(Math.random() * 40)
  }, 100)

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
        results.value = data.results
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
</script>

<style scoped>
.spider-node-container {
  display: flex;
  flex-direction: column;
  width: 340px;
  background: rgba(5, 10, 10, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(0, 255, 65, 0.3);
  border-radius: 12px;
  font-family: 'Inter', 'Space Mono', monospace;
  color: #fff;
  box-shadow: 0 15px 35px rgba(0,0,0,0.6), inset 0 0 20px rgba(0, 255, 65, 0.05);
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.spider-node-container:hover {
  transform: translateY(-2px);
  box-shadow: 0 20px 45px rgba(0,0,0,0.7), inset 0 0 30px rgba(0, 255, 65, 0.15);
  border-color: rgba(0, 255, 65, 0.6);
}

.spider-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: linear-gradient(90deg, rgba(0, 255, 65, 0.1) 0%, transparent 100%);
  border-bottom: 1px solid rgba(255,255,255,0.05);
}

.header-icon {
  font-size: 14px;
  color: #00FF41;
  text-shadow: 0 0 8px #00FF41;
}

.header-title {
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 2px;
  color: rgba(255,255,255,0.9);
  flex: 1;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #333;
  box-shadow: inset 0 0 4px rgba(0,0,0,0.8);
  transition: all 0.3s ease;
}

.status-dot.active {
  background: #00FF41;
  box-shadow: 0 0 10px #00FF41;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.2); opacity: 0.6; }
  100% { transform: scale(1); opacity: 1; }
}

.spider-body {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.spider-input-group {
  display: flex;
  gap: 8px;
}

.sci-input {
  flex: 1;
  background: rgba(0,0,0,0.4);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 4px;
  color: #00FF41;
  padding: 8px 10px;
  font-family: 'Space Mono', monospace;
  font-size: 11px;
  outline: none;
  transition: all 0.2s ease;
}

.sci-input:focus {
  border-color: #00FF41;
  box-shadow: 0 0 10px rgba(0, 255, 65, 0.2);
  background: rgba(0, 255, 65, 0.05);
}

.spider-btn {
  position: relative;
  background: rgba(0, 255, 65, 0.1);
  border: 1px solid rgba(0, 255, 65, 0.4);
  color: #00FF41;
  font-family: 'Space Mono', monospace;
  font-size: 10px;
  font-weight: 800;
  border-radius: 4px;
  padding: 0 14px;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.3s ease;
}

.spider-btn:hover:not(:disabled) {
  background: #00FF41;
  color: #000;
  box-shadow: 0 0 15px rgba(0, 255, 65, 0.4);
}

.spider-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  border-color: rgba(255,255,255,0.2);
  color: rgba(255,255,255,0.5);
  background: transparent;
}

.btn-glitch {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 255, 65, 0.2);
  animation: glitch-anim 0.2s infinite alternate-reverse;
  pointer-events: none;
}

@keyframes glitch-anim {
  0% { transform: translateX(-2px); }
  100% { transform: translateX(2px); }
}

.depth-control {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-top: 8px;
  border-top: 1px dashed rgba(255,255,255,0.1);
}

.depth-labels {
  display: flex;
  justify-content: space-between;
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 1px;
}

.depth-title {
  color: #00FF41;
}

.depth-max {
  color: rgba(255,255,255,0.4);
}

.sci-range {
  -webkit-appearance: none;
  width: 100%;
  height: 4px;
  background: rgba(0,0,0,0.6);
  border-radius: 2px;
  outline: none;
}

.sci-range::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #00FF41;
  cursor: pointer;
  box-shadow: 0 0 8px #00FF41;
  transition: all 0.2s ease;
}

.sci-range::-webkit-slider-thumb:hover {
  transform: scale(1.2);
}

.spider-status {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 10px;
  color: rgba(255,255,255,0.6);
  font-family: 'Space Mono', monospace;
}

.loader-container {
  height: 2px;
  width: 100%;
  background: rgba(255,255,255,0.1);
  overflow: hidden;
  border-radius: 1px;
}

.loader-bar {
  width: 30%;
  height: 100%;
  background: #00FF41;
  box-shadow: 0 0 5px #00FF41;
  animation: scan 1.5s infinite ease-in-out alternate;
}

@keyframes scan {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(350%); }
}

.status-text {
  display: flex;
  justify-content: space-between;
}

.highlight {
  color: #00FF41;
  font-weight: bold;
}

.blink {
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.spider-results {
  display: flex;
  flex-direction: column;
  gap: 8px;
  border: 1px solid rgba(0, 255, 65, 0.2);
  border-radius: 6px;
  background: rgba(0, 255, 65, 0.02);
  padding: 10px;
}

.results-header {
  font-size: 9px;
  font-weight: 900;
  color: #00FF41;
  letter-spacing: 1px;
  border-bottom: 1px solid rgba(0, 255, 65, 0.2);
  padding-bottom: 4px;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 120px;
  overflow-y: auto;
  font-size: 10px;
  font-family: 'Space Mono', monospace;
}

.results-list::-webkit-scrollbar {
  width: 4px;
}
.results-list::-webkit-scrollbar-thumb {
  background: rgba(0, 255, 65, 0.3);
  border-radius: 2px;
}

.result-item {
  color: rgba(255,255,255,0.8);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding: 2px 0;
}

.res-arrow {
  color: #00FF41;
  margin-right: 4px;
  font-weight: bold;
}
</style>

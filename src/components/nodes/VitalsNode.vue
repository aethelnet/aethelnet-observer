<template>
  <div class="vitals-node">
    <div class="header">
      [ SYSTEM VITALS ]
    </div>
    
    <div class="vitals-body">
      <div class="vital-row">
        <span>FPS</span>
        <span :style="{ color: fps > 30 ? '#00FF41' : '#E03C31' }">{{ fps }}</span>
      </div>
      <div class="vital-row">
        <span>MEMORY (HEAP)</span>
        <span>{{ memoryUsage }} MB</span>
      </div>
      <div class="vital-row">
        <span>NETWORK LATENCY</span>
        <span>{{ ping }} ms</span>
      </div>
      <div class="vital-row">
        <span>ACTIVE NODES</span>
        <span>{{ getTotalNodes() }}</span>
      </div>
      
      <div class="vital-row slider-row">
        <span>POWER ALLOC</span>
        <div class="slider-container">
          <span class="slider-label">AI</span>
          <input type="range" min="0" max="100" v-model="resourceAllocation" class="alloc-slider" />
          <span class="slider-label">GFX</span>
        </div>
      </div>

      <div class="chart-container">
        <!-- A simple CSS-based bar chart for FPS history -->
        <div 
          v-for="(val, idx) in fpsHistory" 
          :key="idx" 
          class="bar"
          :style="{ height: Math.min(val, 60) + 'px', background: val > 30 ? '#00FF41' : '#E03C31' }"
        ></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { resourceAllocation } from '../../utils/engineSettings'

const props = defineProps<{
  node: any
}>()

const fps = ref(0)
const memoryUsage = ref(0)
const ping = ref(0)
const fpsHistory = ref<number[]>([])
const MAX_HISTORY = 40

let frameCount = 0
let lastTime = performance.now()
let rafId: number
let pingInterval: number

function getTotalNodes() {
  if (!props.node.meta_data) return '?'
  try {
    const meta = JSON.parse(props.node.meta_data)
    return meta.totalNodes || '?'
  } catch (e) {
    return '?'
  }
}

function updateVitals() {
  const now = performance.now()
  frameCount++
  
  if (now - lastTime >= 1000) {
    fps.value = Math.round((frameCount * 1000) / (now - lastTime))
    frameCount = 0
    lastTime = now
    
    fpsHistory.value.push(fps.value)
    if (fpsHistory.value.length > MAX_HISTORY) {
      fpsHistory.value.shift()
    }
    
    // Update memory if available (Chrome specific, but good for diagnostics)
    if ((performance as any).memory) {
      memoryUsage.value = Math.round((performance as any).memory.usedJSHeapSize / 1048576)
    }
  }
  
  rafId = requestAnimationFrame(updateVitals)
}

async function measurePing() {
  try {
    const start = performance.now()
    const API_BASE = (window as any).API_BASE || ''
    const url = API_BASE ? `${API_BASE}/lgnn/graph?parent_id=ROOT` : `/api/lgnn/graph?parent_id=ROOT`
    // Use HEAD request just to check latency
    await fetch(url, { method: 'HEAD', cache: 'no-cache' })
    const end = performance.now()
    ping.value = Math.round(end - start)
  } catch (e) {
    ping.value = 999
  }
}

onMounted(() => {
  rafId = requestAnimationFrame(updateVitals)
  measurePing()
  pingInterval = window.setInterval(measurePing, 5000)
})

onBeforeUnmount(() => {
  cancelAnimationFrame(rafId)
  clearInterval(pingInterval)
})
</script>

<style scoped>
.vitals-node {
  width: 220px;
  background: var(--color-bg-panel);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-node);
  font-family: var(--font-family-mono);
}

.header {
  padding: 8px;
  background: var(--color-bg-primary);
  border-bottom: 1px solid var(--border-color);
  font-weight: 900;
  font-size: 11px;
  color: #00F3FF;
  text-align: center;
  letter-spacing: 1px;
}

.vitals-body {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.vital-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  font-family: var(--font-family-mono);
  font-size: 11px;
}

.slider-row {
  flex-direction: column;
  gap: 6px;
  margin-top: 10px;
  margin-bottom: 12px;
  padding-top: 8px;
  border-top: 1px solid rgba(0, 243, 255, 0.2);
}

.slider-container {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.slider-label {
  font-size: 9px;
  color: var(--color-accent);
  font-weight: bold;
}

.alloc-slider {
  flex: 1;
  -webkit-appearance: none;
  background: rgba(0, 0, 0, 0.5);
  height: 4px;
  border-radius: 2px;
  outline: none;
}

.alloc-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 12px;
  height: 12px;
  background: var(--color-accent);
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 0 5px var(--color-accent);
}

.chart-container {
  display: flex;
  align-items: flex-end;
  height: 60px;
  gap: 2px;
  margin-top: 10px;
  border-bottom: 1px solid rgba(255,255,255,0.2);
}

.bar {
  flex: 1;
  min-width: 2px;
  transition: height 0.2s ease;
}
</style>

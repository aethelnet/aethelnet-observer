<template>
  <div class="repulsor-node" @mousedown.stop>
    <div class="forcefield" :class="{ 'active': isRepelling }"></div>
    
    <div class="header">
      <div class="title"><i class="fas fa-shield-alt"></i> REPULSOR</div>
      <div class="subtitle">Data Stream Filter</div>
    </div>
    
    <div class="content">
      <div class="filter-controls">
        <label>Repulsion Threshold (Coherence < %)</label>
        <input type="range" min="0" max="100" v-model.number="threshold" class="threshold-slider" />
        <div class="threshold-value">{{ threshold }}%</div>
      </div>

      <div class="stream-monitor">
        <div class="monitor-header">INCOMING STREAM</div>
        <div class="stream-item" v-for="(item, i) in incomingStream" :key="i" :class="{ 'repelled': item.score < threshold, 'accepted': item.score >= threshold }">
          <span class="item-text">{{ item.text }}</span>
          <span class="item-score">[{{ item.score }}%]</span>
          <span class="item-status" v-if="item.score < threshold">BLOCKED</span>
          <span class="item-status" v-else>PASSED</span>
        </div>
      </div>

      <button class="test-btn" @click="testStream" :disabled="isRepelling">
        Test Repulsion Field
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  node: any
}>()

const threshold = ref(75)
const isRepelling = ref(false)

const incomingStream = ref<any[]>([])

const mockStream = [
  { text: "Viral dance trend #1948", score: 12 },
  { text: "New preprint on GNN attention scaling", score: 94 },
  { text: "Clickbait: 'You won't believe what happens next!'", score: 5 },
  { text: "Architectural blueprint for Aethelnet v4", score: 99 }
]

async function testStream() {
  if (isRepelling.value) return
  isRepelling.value = true
  incomingStream.value = []
  
  for (const item of mockStream) {
    incomingStream.value.push(item)
    // Small delay to simulate stream processing
    await new Promise(r => setTimeout(r, 400))
  }
  
  setTimeout(() => {
    isRepelling.value = false
  }, 1000)
}
</script>

<style scoped>
.repulsor-node {
  background: rgba(5, 10, 20, 0.95);
  border: 1px solid rgba(0, 150, 255, 0.4);
  border-radius: 12px;
  width: 300px;
  color: #fff;
  font-family: 'Inter', sans-serif;
  box-shadow: 0 0 20px rgba(0, 150, 255, 0.2);
  position: relative;
  display: flex;
  flex-direction: column;
}

.forcefield {
  position: absolute;
  top: -10px; left: -10px; right: -10px; bottom: -10px;
  border-radius: 16px;
  border: 2px solid transparent;
  pointer-events: none;
  transition: all 0.2s;
}

.forcefield.active {
  border-color: rgba(0, 255, 255, 0.6);
  box-shadow: 0 0 30px rgba(0, 255, 255, 0.4), inset 0 0 20px rgba(0, 255, 255, 0.2);
  animation: pulse 1s infinite alternate;
}

@keyframes pulse {
  0% { transform: scale(1); opacity: 0.8; }
  100% { transform: scale(1.02); opacity: 1; }
}

.header {
  padding: 12px;
  background: linear-gradient(180deg, rgba(0,150,255,0.2) 0%, transparent 100%);
  border-bottom: 1px solid rgba(0, 150, 255, 0.2);
}

.title {
  font-weight: 900;
  color: #00d4ff;
  letter-spacing: 2px;
  font-size: 14px;
}

.subtitle {
  font-size: 10px;
  color: #888;
  margin-top: 4px;
  text-transform: uppercase;
}

.content {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.filter-controls label {
  font-size: 10px;
  color: #00d4ff;
  text-transform: uppercase;
  font-weight: bold;
}

.threshold-slider {
  width: 100%;
  margin-top: 8px;
  accent-color: #00d4ff;
}

.threshold-value {
  text-align: right;
  font-size: 14px;
  font-weight: 900;
  color: #fff;
  margin-top: 4px;
}

.stream-monitor {
  background: rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  padding: 8px;
  min-height: 120px;
  max-height: 200px;
  overflow-y: auto;
}

.monitor-header {
  font-size: 9px;
  color: #555;
  margin-bottom: 8px;
}

.stream-item {
  display: flex;
  align-items: center;
  font-size: 11px;
  padding: 6px;
  border-radius: 4px;
  margin-bottom: 4px;
  background: rgba(255, 255, 255, 0.05);
}

.stream-item.repelled {
  border-left: 3px solid #ff3366;
  opacity: 0.6;
}

.stream-item.accepted {
  border-left: 3px solid #00ff66;
}

.item-text {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-right: 8px;
}

.item-score {
  font-weight: bold;
  margin-right: 8px;
}

.item-status {
  font-size: 9px;
  font-weight: bold;
  padding: 2px 4px;
  border-radius: 2px;
}

.repelled .item-status {
  background: #ff3366;
  color: #000;
}

.accepted .item-status {
  background: #00ff66;
  color: #000;
}

.test-btn {
  background: rgba(0, 150, 255, 0.1);
  border: 1px solid #00d4ff;
  color: #00d4ff;
  padding: 8px;
  border-radius: 4px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s;
}

.test-btn:hover:not(:disabled) {
  background: #00d4ff;
  color: #000;
}

.test-btn:disabled {
  opacity: 0.5;
  cursor: wait;
}
</style>

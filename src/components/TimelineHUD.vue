<template>
  <div class="timeline-hud" :class="{ 'is-expanded': isExpanded }">
    <div class="hud-header" @click="isExpanded = !isExpanded">
      <span class="timeline-title">UNIVERSE SELECTOR</span>
      <button class="expand-btn">{{ isExpanded ? '▼' : '▲' }}</button>
    </div>
    
    <div class="hud-content" v-show="isExpanded">
      <div class="snapshot-controls">
        <input 
          v-model="newSnapshotDesc" 
          placeholder="Describe reality branch..." 
          class="snapshot-input"
          @keydown.enter="createSnapshot('user_manual', '')"
        />
        <button class="btn-fork" @click="createSnapshot('user_manual', '')">[ FORK REALITY ]</button>
      </div>
      
      <div class="timeline-track" v-if="snapshots.length > 0">
        <div 
          v-for="(snap, idx) in snapshots" 
          :key="snap.hash"
          class="timeline-node-wrapper"
        >
          <div 
            class="timeline-node"
            :class="{ 
              'is-active': activeHash === snap.hash,
              'type-auto': snap.commit_type === 'auto',
              'type-compress': snap.commit_type === 'compress',
              'type-user': snap.commit_type === 'user_manual'
            }"
            draggable="true"
            @dragstart="onDragStart($event, snap)"
            @click="checkoutSnapshot(snap.hash)"
            :title="formatDate(snap.timestamp) + '\n' + snap.description"
          ></div>
          <div class="timeline-label" v-if="idx === 0 || idx === snapshots.length - 1 || activeHash === snap.hash">
            {{ snap.description || snap.hash.substring(0, 6) }}
          </div>
          <div class="timeline-line" v-if="idx < snapshots.length - 1"></div>
        </div>
      </div>
      <div v-else class="no-snapshots">
        No reality forks found. Create one to start tracking time.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const isExpanded = ref(false)
const snapshots = ref<any[]>([])
const activeHash = ref<string | null>(null)
const newSnapshotDesc = ref('')

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

const emit = defineEmits(['checkout-complete'])

async function fetchHistory() {
  try {
    const url = API_BASE ? `${API_BASE}/lgnn/snapshot/history` : '/api/lgnn/snapshot/history'
    const res = await fetch(url)
    if (res.ok) {
      const data = await res.json()
      // Sort oldest to newest for the timeline
      snapshots.value = data.history.sort((a: any, b: any) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
      if (snapshots.value.length > 0 && !activeHash.value) {
        activeHash.value = snapshots.value[snapshots.value.length - 1].hash
      }
    }
  } catch (err) {
    console.error("Failed to fetch timeline:", err)
  }
}

async function checkoutSnapshot(hash: string) {
  try {
    const url = API_BASE ? `${API_BASE}/lgnn/snapshot/checkout` : '/api/lgnn/snapshot/checkout'
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ commit_hash: hash })
    })
    if (res.ok) {
      activeHash.value = hash
      emit('checkout-complete')
    }
  } catch (err) {
    console.error("Checkout failed:", err)
  }
}

async function createSnapshot(cType: string = 'user_manual', desc?: string) {
  const finalDesc = desc || newSnapshotDesc.value.trim() || 'Manual Snapshot'
  try {
    const url = API_BASE ? `${API_BASE}/lgnn/snapshot/create` : '/api/lgnn/snapshot/create'
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        description: finalDesc,
        commit_type: cType
      })
    })
    if (res.ok) {
      if (cType === 'user_manual' && !desc) newSnapshotDesc.value = '' 
      await fetchHistory()
    }
  } catch (err) {
    console.error("Fork failed:", err)
  }
}

function formatDate(iso: string) {
  const d = new Date(iso)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function onDragStart(event: DragEvent, snap: any) {
  if (event.dataTransfer) {
    event.dataTransfer.setData('application/json', JSON.stringify({
      type: 'checkpoint',
      hash: snap.hash,
      description: snap.description
    }))
    event.dataTransfer.effectAllowed = 'copy'
  }
}

let autosaveInterval: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  fetchHistory()
  
  // Autosave every 7 minutes (7 * 60 * 1000)
  autosaveInterval = setInterval(() => {
    // Only autosave if the user hasn't typed a custom description currently
    const desc = newSnapshotDesc.value.trim() ? newSnapshotDesc.value.trim() : "Autosave"
    createSnapshot('auto', desc)
  }, 7 * 60 * 1000)
})

onUnmounted(() => {
  if (autosaveInterval) clearInterval(autosaveInterval)
})
</script>

<style scoped>
.timeline-hud {
  position: absolute;
  top: 60px;
  right: 16px;
  width: 280px;
  background: rgba(20, 20, 20, 0.4);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  z-index: 2000;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
  overflow: hidden;
}

.hud-header {
  padding: 10px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.03);
  border-bottom: 1px solid transparent;
}

.timeline-hud.is-expanded .hud-header {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.timeline-title {
  font-family: var(--font-family-mono, monospace);
  font-size: 10px;
  color: var(--color-text-main);
  font-weight: 800;
  letter-spacing: 1px;
}

.expand-btn {
  background: none;
  border: none;
  color: var(--color-text-accent);
  cursor: pointer;
  font-size: 12px;
  transition: transform 0.3s ease;
}

.hud-content {
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: rgba(255, 255, 255, 0.01);
}

.universe-select-wrapper {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.universe-label {
  font-size: 9px;
  color: var(--color-text-accent);
  font-family: var(--font-family-mono);
  font-weight: 800;
}

.snapshot-controls {
  display: flex;
  gap: 8px;
}

.snapshot-input {
  flex: 1;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  color: #fff;
  padding: 6px 12px;
  font-family: var(--font-family-mono);
  font-size: 11px;
}

.snapshot-input:focus {
  outline: none;
  border-color: var(--color-accent);
}

.btn-fork {
  background: var(--color-accent);
  color: var(--color-bg-primary);
  border: none;
  border-radius: 6px;
  font-family: var(--font-family-mono);
  font-size: 11px;
  font-weight: bold;
  padding: 0 16px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-fork:hover {
  background: #fff;
  box-shadow: 0 0 15px var(--color-accent);
}

.timeline-track {
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
  padding-bottom: 20px;
}

.timeline-node-wrapper {
  display: flex;
  align-items: center;
  position: relative;
  flex: 1;
}

.timeline-node-wrapper:last-child {
  flex: 0;
}

.timeline-node {
  width: 14px;
  height: 14px;
  background: var(--color-bg-primary);
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  cursor: pointer;
  z-index: 2;
  transition: all 0.2s ease;
}

.timeline-node.type-auto {
  border-color: #666;
  background: #222;
}
.timeline-node.type-compress {
  border-color: #ff3366;
  background: #551122;
}
.timeline-node.type-user {
  border-color: #ffcc00;
  background: #332200;
  box-shadow: 0 0 8px rgba(255, 204, 0, 0.4);
}

.timeline-node:hover {
  border-color: #fff;
  transform: scale(1.2);
}

.timeline-node.is-active {
  border-color: var(--color-accent);
  background: var(--color-accent);
  box-shadow: 0 0 10px var(--color-accent);
}

.timeline-line {
  flex: 1;
  height: 2px;
  background: rgba(255, 255, 255, 0.1);
  margin: 0 -2px;
  z-index: 1;
}

.timeline-node.is-active.type-auto {
  background: #666;
  box-shadow: 0 0 10px #666;
}
.timeline-node.is-active.type-compress {
  background: #ff3366;
  box-shadow: 0 0 15px #ff3366;
}
.timeline-node.is-active.type-user {
  background: #ffcc00;
  box-shadow: 0 0 20px #ffcc00;
}

.timeline-label {
  position: absolute;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  font-family: var(--font-family-mono);
  font-size: 10px;
  color: rgba(255, 255, 255, 0.6);
  white-space: nowrap;
}

.no-snapshots {
  font-family: var(--font-family-mono);
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  text-align: center;
}
</style>

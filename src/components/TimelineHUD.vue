<template>
  <div class="timeline-hud glass-panel" :class="{ 'is-expanded': isExpanded }">
    <div class="hud-header" @click="isExpanded = !isExpanded">
      <div class="header-left">
        <span class="timeline-title">REALITY FORKS</span>
        <span class="active-badge" v-if="activeHash">#{{ activeHash.substring(0, 6) }}</span>
      </div>
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
        <button class="btn-fork" @click="createSnapshot('user_manual', '')">
          <span class="btn-glow"></span>
          [ FORK REALITY ]
        </button>
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
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useGraphStore } from '../stores/useGraphStore'

const isExpanded = ref(false)
const newSnapshotDesc = ref('')
const emit = defineEmits(['checkout-complete'])

const graphStore = useGraphStore()
const snapshots = computed(() => graphStore.snapshots)
const activeHash = computed(() => graphStore.activeHash)

async function checkoutSnapshot(hash: string) {
  const success = await graphStore.checkoutSnapshot(hash)
  if (success) {
    emit('checkout-complete')
  }
}

async function createSnapshot(cType: string = 'user_manual', desc?: string) {
  const finalDesc = desc || newSnapshotDesc.value.trim() || 'Manual Snapshot'
  await graphStore.createSnapshot(cType, finalDesc)
  if (cType === 'user_manual' && !desc) newSnapshotDesc.value = ''
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
  graphStore.fetchHistory()
  
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
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  width: 400px;
  z-index: 1000;
  border-radius: 16px;
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.08);
  font-family: 'Inter', -apple-system, sans-serif;
}

.timeline-hud.is-expanded {
  width: 600px;
  max-width: 90vw;
}

.hud-header {
  padding: 14px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  background: rgba(250, 250, 252, 0.5);
  border-radius: 16px 16px 0 0;
}

.timeline-hud:not(.is-expanded) .hud-header {
  border-bottom: none;
  border-radius: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.timeline-title {
  font-family: 'Inter', sans-serif;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1px;
  color: #555;
  text-transform: uppercase;
}

.active-badge {
  background: rgba(0, 188, 212, 0.1);
  border: 1px solid rgba(0, 188, 212, 0.2);
  color: #00bcd4;
  font-family: 'Space Mono', monospace;
  font-size: 9px;
  padding: 2px 6px;
  border-radius: 4px;
}

.expand-btn {
  background: none;
  border: none;
  color: #888;
  cursor: pointer;
  font-size: 10px;
  transition: all 0.2s ease;
}

.expand-btn:hover {
  color: #333;
  transform: scale(1.1);
}

.hud-content {
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: transparent;
  border-radius: 0 0 16px 16px;
}

.universe-select-wrapper {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.universe-label {
  font-size: 9px;
  color: #666;
  font-family: 'Space Mono', monospace;
  font-weight: 700;
}

.snapshot-controls {
  display: flex;
  gap: 8px;
}

.snapshot-input {
  flex: 1;
  background: rgba(245, 245, 247, 0.8);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 8px;
  color: #333;
  padding: 8px 14px;
  font-family: 'Inter', sans-serif;
  font-size: 12px;
  transition: all 0.2s ease;
}

.snapshot-input:focus {
  outline: none;
  background: #fff;
  border-color: rgba(0, 188, 212, 0.4);
  box-shadow: 0 0 0 3px rgba(0, 188, 212, 0.1);
}

.btn-fork {
  position: relative;
  background: #fff;
  color: #333;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  font-family: 'Space Mono', monospace;
  font-size: 10px;
  font-weight: 700;
  padding: 0 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  overflow: hidden;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
}

.btn-fork:hover {
  background: #fafafa;
  border-color: rgba(0, 188, 212, 0.4);
  color: #00bcd4;
  box-shadow: 0 4px 12px rgba(0, 188, 212, 0.1);
}

.btn-glow {
  display: none; /* Removed glitch effect for clean UI */
}

.timeline-track {
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
  padding-bottom: 20px;
  margin-top: 8px;
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
  width: 12px;
  height: 12px;
  background: #fff;
  border: 2px solid rgba(0, 0, 0, 0.2);
  border-radius: 50%;
  cursor: pointer;
  z-index: 2;
  transition: all 0.2s ease;
}

.timeline-node.type-auto {
  border-color: #aaa;
  background: #f0f0f0;
}
.timeline-node.type-compress {
  border-color: #ff7799;
  background: #ffeeff;
}
.timeline-node.type-user {
  border-color: #f2c12e;
  background: #fffdf5;
}

.timeline-node:hover {
  border-color: #00bcd4;
  transform: scale(1.2);
}

.timeline-node.is-active {
  border-color: #00bcd4;
  background: #e0f7fa;
  box-shadow: 0 0 0 4px rgba(0, 188, 212, 0.1);
}

.timeline-line {
  flex: 1;
  height: 2px;
  background: rgba(0, 0, 0, 0.08);
  margin: 0 -2px;
  z-index: 1;
}

.timeline-label {
  position: absolute;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  font-family: 'Space Mono', monospace;
  font-size: 10px;
  color: #888;
  white-space: nowrap;
}

.no-snapshots {
  font-family: 'Space Mono', monospace;
  font-size: 11px;
  color: #aaa;
  text-align: center;
  padding: 8px 0;
}
</style>

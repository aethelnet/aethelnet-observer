<template>
  <div class="fusion-reactor-node">
    <div class="reactor-core">
      <div class="plasma-ring" :class="{ 'active': isFusing }"></div>
      <div class="core-center">
        <i class="fas fa-atom"></i>
      </div>
    </div>
    
    <div class="header">
      <div class="title">FUSION REACTOR</div>
      <div class="subtitle">Concept Synthesis Engine</div>
    </div>
    
    <div class="content">
      <div class="drop-zones">
        <div class="input-chamber" :class="{ filled: input1 }">
          <div class="chamber-label">Isotope A</div>
          <div class="chamber-content">{{ input1 || 'Awaiting Data...' }}</div>
        </div>
        <div class="input-chamber" :class="{ filled: input2 }">
          <div class="chamber-label">Isotope B</div>
          <div class="chamber-content">{{ input2 || 'Awaiting Data...' }}</div>
        </div>
      </div>

      <!-- Controls -->
      <div class="controls">
        <button class="ignite-btn" @click="ignite" :disabled="!canFuse || isFusing">
          <span v-if="isFusing">FUSING...</span>
          <span v-else>IGNITE FUSION</span>
        </button>
      </div>

      <!-- Result -->
      <div v-if="fusionResult" class="fusion-result">
        <div class="result-label">Synthesized Core Concept:</div>
        <div class="result-text">{{ fusionResult }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  node: any
  globalNodes?: any[]
  globalLinks?: any[]
}>()

const isFusing = ref(false)
const fusionResult = ref('')

const connectedSources = computed(() => {
  if (!props.globalLinks || !props.globalNodes) return []
  const myId = props.node.id
  
  // Find all links targeting this node
  const incomingLinks = props.globalLinks.filter(l => {
    const tgtId = typeof l.target === 'object' ? l.target.id : l.target
    return tgtId === myId
  })
  
  // Extract content from those source nodes
  const sources = incomingLinks.map(l => {
    const srcId = typeof l.source === 'object' ? l.source.id : l.source
    const sourceNode = props.globalNodes!.find(n => n.id === srcId)
    // If the source is Prisma, it has facts
    if (sourceNode?.facts && sourceNode.facts.length > 0) {
      return sourceNode.facts.join(" | ")
    }
    return sourceNode?.text_content || 'Unknown Concept'
  })
  
  return sources
})

const input1 = computed(() => connectedSources.value[0] || '')
const input2 = computed(() => connectedSources.value[1] || '')

const canFuse = computed(() => input1.value && input2.value)

const API_BASE = (window as any).API_BASE || ''

async function ignite() {
  if (!canFuse.value || isFusing.value) return
  isFusing.value = true
  fusionResult.value = ''
  
  try {
    const res = await fetch(`${API_BASE}/lgnn/fusion/ignite`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        concept_a: input1.value,
        concept_b: input2.value
      })
    })
    
    const data = await res.json()
    if (data.status === 'success') {
      fusionResult.value = data.result
      // Optionally store in the node
      props.node.text_content = data.result
    } else {
      fusionResult.value = 'FUSION FAILED: ' + data.message
    }
  } catch (err) {
    console.error(err)
    fusionResult.value = 'FUSION CRITICAL ERROR'
  } finally {
    isFusing.value = false
  }
}
</script>

<style scoped>
.fusion-reactor-node {
  background: rgba(30, 10, 10, 0.75);
  backdrop-filter: blur(25px) saturate(200%);
  border: 1px solid rgba(239, 68, 68, 0.4);
  border-radius: 16px;
  width: 360px;
  color: #fff;
  font-family: 'Inter', sans-serif;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.8), inset 0 0 30px rgba(239, 68, 68, 0.1);
  overflow: hidden;
  position: relative;
  display: flex;
  flex-direction: column;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.reactor-core {
  position: absolute;
  top: -40px;
  right: -40px;
  width: 120px;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 0;
  pointer-events: none;
}

.plasma-ring {
  position: absolute;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  border: 2px dashed rgba(255, 60, 0, 0.3);
  animation: spin 10s linear infinite;
}

.plasma-ring.active {
  border-color: #ff3c00;
  box-shadow: 0 0 30px #ff3c00, inset 0 0 20px #ff3c00;
  animation: spin 1s linear infinite;
}

.core-center {
  font-size: 24px;
  color: rgba(255, 60, 0, 0.5);
}

.plasma-ring.active + .core-center {
  color: #ff3c00;
  text-shadow: 0 0 10px #ff3c00;
}

@keyframes spin {
  100% { transform: rotate(360deg); }
}

.header {
  padding: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  position: relative;
  z-index: 1;
}

.title {
  font-weight: 700;
  letter-spacing: 1px;
  font-size: 15px;
  color: #f8fafc;
  font-family: 'Space Mono', monospace;
}

.subtitle {
  font-size: 10px;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-top: 2px;
}

.content {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: relative;
  z-index: 1;
}

.drop-zones {
  display: flex;
  gap: 12px;
}

.input-chamber {
  flex: 1;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 8px;
  padding: 10px;
  min-height: 70px;
  transition: all 0.3s ease;
}

.input-chamber.filled {
  border-color: rgba(239, 68, 68, 0.4);
  background: rgba(239, 68, 68, 0.1);
}

.chamber-label {
  font-size: 10px;
  color: #ff3c00;
  text-transform: uppercase;
  margin-bottom: 6px;
  font-weight: bold;
}

.chamber-content {
  font-size: 11px;
  color: #ccc;
  line-height: 1.4;
}

.ignite-btn {
  width: 100%;
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(185, 28, 28, 0.1));
  border: 1px solid rgba(239, 68, 68, 0.6);
  color: #fecaca;
  padding: 14px;
  border-radius: 8px;
  font-weight: bold;
  letter-spacing: 2px;
  cursor: pointer;
  transition: all 0.3s;
  text-transform: uppercase;
  font-family: 'Space Mono', monospace;
  box-shadow: 0 4px 15px rgba(239, 68, 68, 0.2);
}

.ignite-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.4), rgba(185, 28, 28, 0.3));
  box-shadow: 0 0 25px rgba(239, 68, 68, 0.5);
  border-color: #f87171;
}

.ignite-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  border-color: #555;
  color: #555;
}

.fusion-result {
  background: rgba(255, 60, 0, 0.1);
  border-left: 3px solid #ff3c00;
  padding: 12px;
  border-radius: 0 8px 8px 0;
  animation: explodeIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
}

.result-label {
  font-size: 10px;
  color: #ff3c00;
  text-transform: uppercase;
  font-weight: bold;
  margin-bottom: 6px;
}

.result-text {
  font-size: 12px;
  color: #fff;
  line-height: 1.5;
  font-weight: 500;
}

@keyframes explodeIn {
  0% { transform: scale(0.9); opacity: 0; filter: brightness(2); }
  100% { transform: scale(1); opacity: 1; filter: brightness(1); }
}
</style>

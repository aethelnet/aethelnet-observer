<template>
  <div class="fusion-reactor-node glass-panel">
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
  background: var(--color-bg-primary);
  width: 100%;
  height: 100%;
  color: var(--color-text-main);
  font-family: var(--font-family);
  display: flex;
  flex-direction: column;
}

.reactor-core {
  display: none; /* Hide the glowing core in brutalism */
}

.header {
  padding: 16px;
  background: #ffffff;
  border-bottom: 2px solid #000000;
}

.title {
  font-weight: bold;
  letter-spacing: 1px;
  font-size: 18px;
  color: #000000;
  font-family: var(--font-family-mono);
  text-transform: uppercase;
}

.subtitle {
  font-size: 12px;
  color: #000000;
  text-transform: uppercase;
  font-weight: bold;
  margin-top: 4px;
}

.content {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: #ffffff;
  flex: 1;
}

.drop-zones {
  display: flex;
  gap: 12px;
}

.input-chamber {
  flex: 1;
  background: #ffffff;
  border: 2px solid #000000;
  padding: 12px;
  min-height: 80px;
}

.input-chamber.filled {
  background: #f0f0f0;
  box-shadow: 4px 4px 0px #000000;
}

.chamber-label {
  font-size: 12px;
  color: #000000;
  text-transform: uppercase;
  margin-bottom: 8px;
  font-weight: bold;
}

.chamber-content {
  font-size: 14px;
  color: #000000;
  line-height: 1.5;
  word-break: break-word;
}

.ignite-btn {
  width: 100%;
  background: #ffffff;
  border: 2px solid #000000;
  color: #000000;
  padding: 16px;
  border-radius: 0;
  font-weight: bold;
  font-size: 16px;
  cursor: pointer;
  text-transform: uppercase;
  font-family: var(--font-family-mono);
  box-shadow: 2px 2px 0px #000000;
}

.ignite-btn:hover:not(:disabled) {
  background: #000000;
  color: #ffffff;
  transform: translate(-2px, -2px);
  box-shadow: 4px 4px 0px #000000;
}

.ignite-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
}

.fusion-result {
  background: #ffffff;
  border: 2px solid #000000;
  padding: 16px;
  box-shadow: 2px 2px 0px #000000;
  margin-top: 16px;
}

.result-label {
  font-size: 12px;
  color: #000000;
  text-transform: uppercase;
  font-weight: bold;
  margin-bottom: 8px;
}

.result-text {
  font-size: 14px;
  color: #000000;
  line-height: 1.5;
  font-weight: bold;
  word-break: break-word;
}
</style>

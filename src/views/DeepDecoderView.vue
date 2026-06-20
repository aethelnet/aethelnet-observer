<template>
  <div class="deep-decoder">
    <div class="decoder-header">
      <span class="title">DEEP DECODER</span>
      <span class="status" :class="{ active: hasInputs }">{{ hasInputs ? 'ANALYZING' : 'IDLE' }}</span>
    </div>
    
    <div class="content-panel">
      <div v-if="!hasInputs" class="idle-text">
        Waiting for synaptic input...<br/>
        (Connect a node to inspect)
      </div>
      <div v-else class="result-panel">
        
        <div class="stream-selector">
          <button @click="activeIndex = Math.max(0, activeIndex - 1)" :disabled="activeIndex === 0">&lt;</button>
          <span>Stream {{ activeIndex + 1 }} / {{ inputNodes.length }}</span>
          <button @click="activeIndex = Math.min(inputNodes.length - 1, activeIndex + 1)" :disabled="activeIndex === inputNodes.length - 1">&gt;</button>
        </div>

        <div class="node-title">{{ activeNode?.label || activeNode?.id || 'Unknown Node' }}</div>
        
        <div class="tabs">
          <button :class="{active: activeTab === 'raw'}" @click="activeTab = 'raw'">RAW DATA</button>
          <button :class="{active: activeTab === 'meta'}" @click="activeTab = 'meta'">METADATA</button>
          <button :class="{active: activeTab === 'chem'}" @click="activeTab = 'chem'" v-if="isChemistry">CHEMISTRY</button>
        </div>

        <div class="tab-content" v-if="activeTab === 'raw'">
          <pre class="raw-text">{{ activeValue }}</pre>
        </div>

        <div class="tab-content" v-if="activeTab === 'meta'">
          <div class="data-row"><strong>Type:</strong> <span>{{ activeNode?.node_type || 'default' }}</span></div>
          <div class="data-row"><strong>Confidence:</strong> <span>{{ activeNode?.confidence !== undefined ? activeNode.confidence.toFixed(4) : 'N/A' }}</span></div>
          <div class="data-row"><strong>Entropy:</strong> <span>{{ activeNode?.entropy !== undefined ? activeNode.entropy.toFixed(4) : 'N/A' }}</span></div>
          <div class="data-row"><strong>Source:</strong> <span>{{ activeNode?.source_tag || 'user' }}</span></div>
          
          <div class="tensor-preview" v-if="activeNode?.tensor">
            <strong>Tensor Signature:</strong>
            <div class="tensor-bars">
              <div v-for="(val, i) in activeNode.tensor.slice(0, 32)" :key="i" class="t-bar" :style="{ height: Math.abs(val)*100 + '%', background: val > 0 ? '#00FF41' : '#E03C31' }"></div>
            </div>
          </div>
        </div>

        <div class="tab-content" v-if="activeTab === 'chem'">
           <div class="mass-display">
            <span class="label">MOLAR MASS</span>
            <span class="value">{{ totalMass.toFixed(2) }} <small>g/mol</small></span>
          </div>
          <div class="element-grid">
            <div v-for="(el, i) in parsedElements" :key="i" class="element-box">
              <div class="el-symbol">{{ el.symbol }}</div>
              <div class="el-details">
                <div>{{ el.name || 'Unknown' }}</div>
                <div>Qty: {{ el.count }}</div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineProps, ref, watch } from 'vue'

const props = defineProps<{
  inputs: Record<string, any>
}>()

const activeIndex = ref(0)
const activeTab = ref('raw')

const inputNodes = computed(() => {
  return Object.values(props.inputs || {}).filter(v => v && v.node);
})

const hasInputs = computed(() => inputNodes.value.length > 0)

const activeData = computed(() => {
  if (inputNodes.value.length === 0) return null;
  if (activeIndex.value >= inputNodes.value.length) activeIndex.value = 0;
  return inputNodes.value[activeIndex.value];
})

const activeNode = computed(() => activeData.value?.node)
const activeValue = computed(() => {
  const val = activeData.value?.value;
  return typeof val === 'object' ? JSON.stringify(val, null, 2) : String(val);
})

watch(activeNode, () => {
  if (isChemistry.value) activeTab.value = 'chem';
  else if (activeTab.value === 'chem') activeTab.value = 'raw';
})

// --- Chemistry Fallback ---
const periodicTable: Record<string, {name: string, weight: number}> = {
  "H": { name: "Hydrogen", weight: 1.008 },
  "C": { name: "Carbon", weight: 12.011 },
  "N": { name: "Nitrogen", weight: 14.007 },
  "O": { name: "Oxygen", weight: 15.999 },
  "Na": { name: "Sodium", weight: 22.990 },
  "S": { name: "Sulfur", weight: 32.06 },
  "P": { name: "Phosphorus", weight: 30.974 },
  "K": { name: "Potassium", weight: 39.098 },
  "Ca": { name: "Calcium", weight: 40.078 },
  "Fe": { name: "Iron", weight: 55.845 },
  "As": { name: "Arsenic", weight: 74.922 }
}

const isChemistry = computed(() => {
  if (!activeValue.value) return false;
  // Simple heuristic: Looks like a chemical formula (e.g. H2O, C6H12O6)
  return /^[A-Z][a-z]?\d*(?:[A-Z][a-z]?\d*)+$/.test(activeValue.value.trim());
})

const parsedElements = computed(() => {
  if (!isChemistry.value) return []
  const matches = activeValue.value.match(/[A-Z][a-z]?\d*/g) || []
  return matches.map(m => {
    const symbolMatch = m.match(/[A-Z][a-z]?/)
    const countMatch = m.match(/\d+/)
    const symbol = symbolMatch ? symbolMatch[0] : m
    const count = countMatch ? parseInt(countMatch[0], 10) : 1
    const info = periodicTable[symbol] || { name: 'Unknown', weight: 0 }
    return { symbol, count, name: info.name, weight: info.weight }
  })
})

const totalMass = computed(() => {
  return parsedElements.value.reduce((acc, el) => acc + (el.weight * el.count), 0)
})
</script>

<style scoped>
.deep-decoder {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #050505;
  color: #F4F4F0;
  font-family: 'Space Mono', monospace;
  border: 1px solid #1A1A1A;
}

.decoder-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #1A1A1A;
  border-bottom: 2px solid #333;
}

.title {
  font-weight: bold;
  font-size: 14px;
  letter-spacing: 1px;
}

.status {
  font-size: 10px;
  padding: 2px 6px;
  background: #333;
  color: #888;
  border-radius: 2px;
}

.status.active {
  background: #00FF41;
  color: #1A1A1A;
}

.content-panel {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
}

.idle-text {
  color: #999;
  font-size: 12px;
  text-align: center;
  margin-top: 20px;
  font-style: italic;
}

.stream-selector {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  font-size: 10px;
  font-weight: bold;
  background: #E8E8E8;
  padding: 4px;
}

.stream-selector button {
  background: #1A1A1A;
  color: #FFF;
  border: none;
  cursor: pointer;
  padding: 2px 8px;
  font-family: inherit;
}

.stream-selector button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.main-formula {
  font-size: 24px;
  font-weight: 900;
  text-align: center;
  margin-bottom: 16px;
  word-break: break-all;
}

.mass-display {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #E8E8E8;
  border: 2px solid #1A1A1A;
  padding: 8px 12px;
  margin-bottom: 16px;
}

.mass-display .label {
  font-size: 10px;
  font-weight: bold;
}

.mass-display .value {
  font-size: 16px;
  font-weight: 900;
  color: #E03C31;
}

.element-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.element-box {
  display: flex;
  border: 2px solid #1A1A1A;
  background: #FFF;
}

.el-symbol {
  background: #1A1A1A;
  color: #FFF;
  font-weight: bold;
  font-size: 16px;
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 40px;
}

.el-details {
  padding: 4px 8px;
  font-size: 10px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
</style>

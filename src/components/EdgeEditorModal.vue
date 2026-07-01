<template>
  <div class="edge-editor-overlay" @mousedown.self="$emit('close')">
    <div class="edge-editor-modal">
      <div class="modal-header">
        <span class="modal-title">SYNAPTIC LINK EDITOR</span>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>

      <div class="modal-body" v-if="link">
        <div class="link-nodes">
          <div class="node-badge source">{{ sourceLabel }}</div>
          <div class="arrow">→</div>
          <div class="node-badge target">{{ targetLabel }}</div>
        </div>

        <div class="control-group">
          <label>CONNECTION STRENGTH (WEIGHT)</label>
          <div class="slider-container">
            <input 
              type="range" 
              v-model.number="currentWeight" 
              min="-1" 
              max="1" 
              step="0.05" 
              class="weight-slider"
            />
            <span class="weight-val" :class="{ negative: currentWeight < 0 }">{{ currentWeight.toFixed(2) }}</span>
          </div>
          <p class="help-text">Adjust the resonance or dissonance between these two nodes. Negative weights create repulsive forces.</p>
        </div>

        <div class="actions">
          <button class="btn btn-danger" @click="handleSever">SEVER LINK</button>
          <div style="flex: 1"></div>
          <button class="btn btn-primary" @click="handleSave">APPLY MUTATION</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

const props = defineProps<{
  link: any
}>()

const emit = defineEmits(['close', 'save', 'sever'])

const currentWeight = ref(1.0)

onMounted(() => {
  if (props.link && typeof props.link.weight === 'number') {
    currentWeight.value = props.link.weight
  }
})

const sourceLabel = computed(() => {
  if (!props.link) return 'Unknown'
  const src = props.link.source
  if (!src) return 'Unknown'
  return typeof src === 'string' ? src.substring(0, 8) : String(src.label || src.id || 'Unknown').substring(0, 8)
})

const targetLabel = computed(() => {
  if (!props.link) return 'Unknown'
  const tgt = props.link.target
  if (!tgt) return 'Unknown'
  return typeof tgt === 'string' ? tgt.substring(0, 8) : String(tgt.label || tgt.id || 'Unknown').substring(0, 8)
})

function handleSave() {
  emit('save', { link: props.link, weight: currentWeight.value })
  emit('close')
}

function handleSever() {
  emit('sever', props.link)
  emit('close')
}
</script>

<style scoped>
.edge-editor-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.6);
  z-index: 20000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.edge-editor-modal {
  width: 400px;
  background: rgba(20, 20, 20, 0.6);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 24px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
  font-family: var(--font-family-mono, monospace);
  color: var(--color-text-main);
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  background: rgba(0, 0, 0, 0.2);
}

.modal-title {
  font-size: 12px;
  font-weight: bold;
  color: #00FF41;
  letter-spacing: 1px;
}

.close-btn {
  background: transparent;
  border: none;
  color: #888;
  cursor: pointer;
  font-size: 14px;
}
.close-btn:hover { color: #FFF; }

.modal-body {
  padding: 24px 16px;
}

.link-nodes {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-bottom: 32px;
}

.node-badge {
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  font-size: 14px;
  color: var(--color-text-main);
}

.arrow {
  color: #666;
  font-size: 18px;
}

.control-group {
  margin-bottom: 32px;
}

.control-group label {
  display: block;
  font-size: 10px;
  color: #888;
  margin-bottom: 12px;
  letter-spacing: 1px;
}

.slider-container {
  display: flex;
  align-items: center;
  gap: 16px;
}

.weight-slider {
  flex: 1;
  accent-color: #00FF41;
}

.weight-val {
  font-size: 14px;
  font-weight: bold;
  color: #00FF41;
  width: 48px;
  text-align: right;
}
.weight-val.negative {
  color: #FF3366;
}

.help-text {
  font-size: 11px;
  color: #666;
  margin-top: 12px;
  line-height: 1.4;
}

.actions {
  display: flex;
  gap: 12px;
}

.btn {
  padding: 10px 16px;
  border-radius: 12px;
  font-weight: 800;
  font-size: 12px;
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
  font-family: var(--font-family-mono, monospace);
}

.btn-primary {
  background: rgba(0, 255, 65, 0.1);
  color: #00FF41;
  border-color: rgba(0, 255, 65, 0.3);
}
.btn-primary:hover {
  background: rgba(0, 255, 65, 0.2);
}

.btn-danger {
  background: rgba(224, 60, 49, 0.1);
  color: #E03C31;
  border-color: rgba(224, 60, 49, 0.3);
}
.btn-danger:hover {
  background: rgba(224, 60, 49, 0.2);
}
</style>

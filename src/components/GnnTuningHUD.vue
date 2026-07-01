<template>
  <div class="gnn-tuning-hud" :class="{ 'is-expanded': isExpanded }">
    <div class="hud-header" @click="isExpanded = !isExpanded">
      <span class="hud-title">GNN PARAMETERS TUNING</span>
      <button class="expand-btn">{{ isExpanded ? '▼' : '▲' }}</button>
    </div>
    
    <div class="hud-content" v-show="isExpanded">
      <div class="tuning-row">
        <div class="tuning-label">
          <span>DECAY RATE:</span>
          <span class="tuning-val">{{ decay.toFixed(3) }}</span>
        </div>
        <input 
          type="range" 
          min="0.01" 
          max="0.5" 
          step="0.01" 
          :value="decay" 
          @input="$emit('update:decay', parseFloat(($event.target as HTMLInputElement).value))"
          @change="$emit('change')"
          class="cyber-slider"
        />
      </div>
      <div class="tuning-row">
        <div class="tuning-label">
          <span>RESONANCE THRESHOLD:</span>
          <span class="tuning-val">{{ resonance.toFixed(2) }}</span>
        </div>
        <input 
          type="range" 
          min="0.1" 
          max="2.0" 
          step="0.05" 
          :value="resonance" 
          @input="$emit('update:resonance', parseFloat(($event.target as HTMLInputElement).value))"
          @change="$emit('change')"
          class="cyber-slider"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  decay: number;
  resonance: number;
}>()

const emit = defineEmits(['update:decay', 'update:resonance', 'change'])

const isExpanded = ref(false)
</script>

<style scoped>
/* GNN Tuning HUD (Premium Glassmorphism) */
.gnn-tuning-hud {
  position: absolute;
  bottom: 140px;
  right: 24px;
  width: 280px;
  background: rgba(10, 10, 15, 0.85);
  border: 1px solid var(--color-accent, #00f3ff);
  border-radius: 12px;
  z-index: 2000;
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 30px rgba(0, 243, 255, 0.1);
  transition: all 0.3s ease;
  overflow: hidden;
}

.hud-header {
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  background: rgba(0, 243, 255, 0.05);
  border-bottom: 1px solid transparent;
}

.gnn-tuning-hud.is-expanded .hud-header {
  border-bottom: 1px solid rgba(0, 243, 255, 0.2);
}

.hud-title {
  font-family: var(--font-family-mono, monospace);
  font-size: 11px;
  color: var(--color-accent, #00f3ff);
  font-weight: bold;
  letter-spacing: 1px;
}

.expand-btn {
  background: none;
  border: none;
  color: var(--color-accent, #00f3ff);
  cursor: pointer;
  font-size: 10px;
}

.hud-content {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.tuning-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tuning-label {
  font-family: var(--font-family-mono, monospace);
  font-size: 11px;
  color: rgba(255, 255, 255, 0.7);
  display: flex;
  justify-content: space-between;
}

.tuning-val {
  color: var(--color-accent, #00f3ff);
  font-weight: bold;
}

.cyber-slider {
  -webkit-appearance: none;
  background: rgba(255, 255, 255, 0.1);
  height: 4px;
  border-radius: 2px;
  outline: none;
  width: 100%;
}

.cyber-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--color-accent, #00f3ff);
  cursor: pointer;
  box-shadow: 0 0 10px var(--color-accent, #00f3ff);
}
</style>

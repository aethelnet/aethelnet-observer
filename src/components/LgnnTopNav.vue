<template>
  <nav role="navigation" aria-label="Main Navigation" class="top-nav-glass">
    <!-- Active Persona Switcher -->
    <div class="nav-container">
      <span style="font-size: 10px; font-weight: 800; color: var(--color-text-accent);">MASK:</span>
      <select :value="globalActivePersonaId" @change="$emit('update:globalActivePersonaId', $event.target.value)" class="nav-select">
        <option value="">[ SYSTEM ]</option>
        <option v-for="idNode in identityNodes" :key="idNode.id" :value="idNode.id">{{ idNode.label }}</option>
      </select>
      <button class="nav-btn-small" @click="$emit('add-mask')" title="Add New Mask">
        +
      </button>
      <button v-if="globalActivePersonaId" class="nav-btn-small" @click="$emit('edit-mask', globalActivePersonaId)" title="Edit Active Mask">
        [E]
      </button>
      <button v-if="globalActivePersonaId" class="nav-btn-small" @click="$emit('remove-mask', globalActivePersonaId)" title="Remove Active Mask" style="color: var(--color-danger, #e03c31);">
        [-]
      </button>
    </div>

    <div style="display: flex; gap: 4px; align-items: center;">
      <button class="nav-btn" @click="$emit('update:showAutonomous', !showAutonomous)" :style="{ color: showAutonomous ? '#00FF41' : '#F2C12E', borderColor: showAutonomous ? '#00FF41' : '#F2C12E' }">
        {{ showAutonomous ? '[ GALAXY VIEW ]' : '[ LOCAL VIEW ]' }}
      </button>
      <div v-if="showAutonomous" class="nav-container">
        <span style="font-size: 10px; font-weight: 900; color: var(--color-text-main);">MIN CONF:</span>
        <input type="range" min="0" max="1" step="0.05" :value="minConfidence" @input="$emit('update:minConfidence', parseFloat($event.target.value))" style="width: 80px; accent-color: var(--color-accent);" />
        <span style="font-size: 10px; font-weight: 900; color: var(--color-accent); width: 20px;">{{ minConfidence.toFixed(2) }}</span>
      </div>
    </div>
    
    <button class="nav-btn" @click="$emit('recenter')">
      RECENTER
    </button>
    
    <!-- Navigation Buttons -->
    <button class="nav-btn" @click="$emit('toggle-assets')">
      [ ASSETS ]
    </button>
    <button class="nav-btn" @click="$emit('toggle-grid')" :class="{ 'wip-active': isGridMode }">
      [ GRID ]
    </button>
    <button class="nav-btn" @click="$emit('toggle-spiders')">
      [ SPIDERS ]
    </button>

    <!-- Eco Mode and Help hidden for now -->
  </nav>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue'

const props = defineProps<{
  identityNodes: any[];
  globalActivePersonaId: string;
  showAutonomous: boolean;
  minConfidence: number;
  isGridMode: boolean;
  showHelpOverlay: boolean;
  isEcoMode?: boolean;
}>()

const emits = defineEmits([
  'update:globalActivePersonaId',
  'update:showAutonomous',
  'update:minConfidence',
  'update:showHelpOverlay',
  'recenter',
  'toggle-grid',
  'toggle-assets',
  'toggle-spiders',
  'toggle-eco',
  'add-mask',
  'edit-mask',
  'remove-mask'
])
</script>

<style scoped>
.top-nav-glass {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 2000;
  display: flex;
  gap: 8px;
  align-items: center;
  background: rgba(20, 20, 20, 0.4);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.05);
  padding: 6px 12px;
  border-radius: 20px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
}

.nav-container {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.03);
  padding: 2px 8px;
  border-radius: 12px;
}

.nav-select {
  background: transparent;
  border: none;
  outline: none;
  font-family: var(--font-family-mono);
  font-size: 10px;
  font-weight: 800;
  color: var(--color-text-main);
  cursor: pointer;
  max-width: 120px;
}

.nav-select option {
  background: var(--color-bg-panel);
  color: var(--color-text-main);
}

.nav-btn {
  font-family: 'Space Mono', var(--font-family-mono);
  border: 1px solid var(--border-color);
  border-radius: 0;
  font-weight: 800;
  background: var(--color-bg-panel);
  color: var(--color-text-main);
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  color: var(--color-text-main);
  font-family: var(--font-family-mono);
  font-size: 9px;
  font-weight: 600;
  padding: 4px 10px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s ease;
}

.nav-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
}

.nav-btn.wip-active {
  background: rgba(0, 255, 65, 0.1);
  border-color: rgba(0, 255, 65, 0.3);
  color: #00FF41;
}

.nav-btn-small {
  background: transparent;
  border: none;
  color: var(--color-text-accent);
  font-family: var(--font-family-mono);
  font-size: 9px;
  font-weight: 800;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.nav-btn-small:hover {
  background: rgba(255, 255, 255, 0.1);
}

.nav-btn-active {
  background: var(--color-text-main);
  color: var(--color-bg-primary);
}

.nav-btn:hover {
  background: var(--color-bg-hover);
  color: var(--color-text-main);
}

.wip-btn {
  border-style: dashed !important;
  color: #FF9800 !important;
  border-color: #FF9800 !important;
  opacity: 0.8;
}

.wip-btn:hover {
  background: rgba(255, 152, 0, 0.1) !important;
  opacity: 1;
}

.wip-active {
  background: rgba(255, 152, 0, 0.2) !important;
  border-style: solid !important;
}
</style>

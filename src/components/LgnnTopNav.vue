<template>
  <nav role="navigation" aria-label="Main Navigation" style="position: absolute; top: 16px; right: 16px; z-index: 2000; display: flex; gap: 8px; align-items: center;">
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
      <button class="nav-btn" @click="$emit('update:showAutonomous', !showAutonomous)">
        {{ showAutonomous ? 'HIDE SPIDER NODES' : 'SHOW SPIDER NODES' }}
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
    
    <button class="nav-btn" @click="$emit('toggle-grid')" :class="{ 'nav-btn-active': isGridMode }">
      [ GRID ]
    </button>
    
    <button class="nav-btn" @click="$emit('toggle-assets')">
      [ ASSETS ]
    </button>

    <button class="nav-btn" @click="$emit('toggle-eco')" :class="{ 'nav-btn-active': isEcoMode }" style="color: #4CAF50; border-color: #4CAF50;">
      [ ECO MODE ]
    </button>

    <button class="nav-btn" @click="$emit('update:showHelpOverlay', !showHelpOverlay)">
      [ ? ]
    </button>
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
  'toggle-eco',
  'add-mask',
  'edit-mask',
  'remove-mask'
])
</script>

<style scoped>
.nav-container {
  display: flex;
  align-items: center;
  gap: 4px;
  border: 1px solid var(--border-color);
  padding: 4px 8px;
  background: var(--color-bg-panel);
  box-shadow: var(--shadow-node);
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
  cursor: pointer;
  box-shadow: var(--shadow-node);
  padding: 4px 8px;
  transition: all var(--transition-fast);
}

.nav-btn-small {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--color-text-main);
  font-family: var(--font-family-mono);
  font-weight: 900;
  cursor: pointer;
  padding: 0 4px;
  margin-left: 4px;
}
.nav-btn-small:hover {
  background: var(--color-text-main);
  color: var(--color-bg-panel);
}

.nav-btn:hover {
  background: var(--color-text-main);
  color: var(--color-bg-primary);
  transform: translate(-1px, -1px);
  box-shadow: 3px 3px 0px var(--border-color);
}

.nav-btn:active {
  transform: translate(1px, 1px);
  box-shadow: 1px 1px 0px var(--border-color);
}

.nav-btn-active {
  background: var(--color-text-main);
  color: var(--color-bg-primary);
}

.nav-btn-active:hover {
  background: var(--color-bg-panel);
  color: var(--color-text-main);
}
</style>

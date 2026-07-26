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
    
    <div v-if="authStore.isConnected" class="nav-container" style="background: #fff; border: 2px solid #000; box-shadow: 4px 4px 0px #000; border-radius: 0;">
      <span style="font-size: 10px; font-weight: 800; color: #000;">PUBLIC:</span>
      <span style="font-size: 11px; font-weight: 900; color: #000;">{{ parseFloat(authStore.aethelBalance).toFixed(0) }}</span>
      <span style="font-size: 10px; font-weight: 800; color: #000; margin-left: 8px;">SHIELDED:</span>
      <span style="font-size: 11px; font-weight: 900; color: #fff; background: #000; padding: 2px 4px;">{{ parseFloat(authStore.shieldedBalance).toFixed(0) }}</span>
      <span style="font-size: 10px; font-weight: 800; color: #000;">AETHEL</span>
    </div>

    <button class="nav-btn" @click="authStore.connectWallet()" :class="{ 'nav-btn-active': authStore.isConnected }" style="margin-left: auto;">
      {{ authStore.isConnected ? `[ ${authStore.shortAddress} ]` : '[ CONNECT WALLET ]' }}
    </button>
  </nav>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue'
import { useAuthStore } from '../stores/authStore'

const authStore = useAuthStore()

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
  background: #ffffff;
  border: 2px solid #000000;
  padding: 8px 16px;
  border-radius: 0;
  box-shadow: 4px 4px 0px #000000;
  font-family: 'Space Mono', monospace;
}

.nav-container {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #ffffff;
  padding: 4px 10px;
  border-radius: 0;
  border: 2px solid #000000;
}

.nav-select {
  background: transparent;
  border: none;
  outline: none;
  font-family: 'Inter', sans-serif;
  font-size: 11px;
  font-weight: 600;
  color: #333;
  cursor: pointer;
  max-width: 140px;
}

.nav-select option {
  background: #fff;
  color: #333;
}

.nav-btn {
  background: #ffffff;
  border: 2px solid #000000;
  border-radius: 0;
  color: #000000;
  font-family: 'Space Mono', monospace;
  font-size: 11px;
  font-weight: 600;
  padding: 6px 14px;
  cursor: pointer;
  white-space: nowrap;
  transition: none;
  box-shadow: 2px 2px 0px #000000;
}

.nav-btn:hover {
  background: #000000;
  border-color: #000000;
  color: #ffffff;
  transform: translate(-2px, -2px);
  box-shadow: 4px 4px 0px #000000;
}

.nav-btn.wip-active {
  background: #000000;
  border-color: #000000;
  color: #ffffff;
}

.nav-btn-small {
  background: transparent;
  border: none;
  color: #888;
  font-family: 'Space Mono', monospace;
  font-size: 9px;
  font-weight: 700;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.nav-btn-small:hover {
  background: rgba(0, 0, 0, 0.04);
  color: #333;
}

.nav-btn-active {
  background: #333;
  color: #fff;
}

.wip-btn {
  border-style: dashed !important;
  color: #888 !important;
  border-color: #ddd !important;
}

.wip-btn:hover {
  background: rgba(0, 0, 0, 0.02) !important;
  color: #555 !important;
  border-color: #bbb !important;
}

.wip-active {
  background: rgba(0, 188, 212, 0.1) !important;
  border-style: solid !important;
  color: #00bcd4 !important;
  border-color: rgba(0, 188, 212, 0.3) !important;
}
</style>

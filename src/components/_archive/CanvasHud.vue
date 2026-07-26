<template>
  <div class="canvas-hud-container">
    <!-- Chromatic Toggle Button -->
    <button class="hud-btn chromatic-toggle" @click.stop="$emit('toggle-chromatic')" title="Toggle Chromatic Plasma">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
    </button>
    
    <!-- Observer Mode Toggle -->
    <button class="hud-btn observer-toggle" @click.stop="$emit('enter-observer')" title="Enter Observer Mode">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"></path><circle cx="12" cy="12" r="3"></circle></svg>
    </button>

    <!-- Subconscious Mode Toggle -->
    <button class="hud-btn subconscious-toggle" :class="{ 'is-active': isSubconscious }" @click.stop="$emit('toggle-subconscious')" title="Toggle Subconscious Depth Fusion">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"></path></svg>
    </button>
    
    <!-- Breadcrumbs HUD -->
    <div class="breadcrumbs-hud" v-if="breadcrumbs.length > 1">
      <span v-for="(crumb, i) in breadcrumbs" :key="crumb.id">
        <span class="crumb" @click.stop="$emit('navigate-up', i)">{{ crumb.label }}</span>
        <span v-if="i < breadcrumbs.length - 1" class="crumb-separator">/</span>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue';

const props = defineProps<{
  isChromaticMode: boolean;
  isSubconscious: boolean;
  breadcrumbs: Array<{ id: string, label: string }>;
}>();

const emit = defineEmits(['toggle-chromatic', 'enter-observer', 'toggle-subconscious', 'navigate-up']);
</script>

<style scoped>
.canvas-hud-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 0;
  pointer-events: none;
  z-index: 1000;
}

.hud-btn {
  position: absolute;
  top: 20px;
  background: rgba(30, 30, 30, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #e0e0e0;
  cursor: pointer;
  border-radius: 8px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: auto;
  transition: all 0.2s ease;
  backdrop-filter: blur(8px);
}

.hud-btn:hover {
  background: rgba(60, 60, 60, 0.8);
  color: #fff;
  border-color: rgba(255, 255, 255, 0.3);
}

.hud-btn.is-active {
  background: rgba(16, 185, 129, 0.7);
  color: #ffffff;
  border-color: rgba(16, 185, 129, 0.9);
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.4);
}

.chromatic-toggle {
  right: 20px;
}

.observer-toggle {
  right: 70px;
}

.subconscious-toggle {
  right: 120px;
}

.breadcrumbs-hud {
  position: absolute;
  top: 20px;
  left: 20px;
  background: rgba(30, 30, 30, 0.8);
  padding: 8px 16px;
  border-radius: 20px;
  font-family: var(--font-family-header);
  font-size: 0.9rem;
  color: #a0a0a0;
  pointer-events: auto;
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(8px);
}

.crumb {
  cursor: pointer;
  color: #e0e0e0;
  transition: color 0.2s ease;
}

.crumb:hover {
  color: #3b82f6;
  text-decoration: underline;
}

.crumb-separator {
  margin: 0 8px;
  color: #555;
}
</style>

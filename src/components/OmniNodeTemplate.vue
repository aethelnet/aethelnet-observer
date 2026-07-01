<template>
  <div class="hologram-container">
    <div class="holo-core" :class="{ 'is-light': theme === 'light' }" :style="{ borderColor: color }">
      <div class="holo-title" :style="{ color: color }">{{ title }}</div>
      <div class="holo-matrix">
        <slot></slot>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps } from 'vue';

const props = defineProps({
  title: { type: String, default: 'OMNI NODE' },
  color: { type: String, default: '#00ffa3' },
  theme: { type: String, default: 'dark' } 
});
</script>

<style scoped>
.hologram-container {
  width: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: var(--transition-smooth);
  pointer-events: auto;
}

.holo-core {
  width: 100%;
  padding: 20px;
  border-radius: 12px;
  background: var(--color-bg-card);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-md);
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  color: var(--color-text, #ffffff);
}

.holo-core.is-light {
  background: rgba(255, 255, 255, 0.92) !important;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05) !important;
  color: #1e293b !important;
}

.holo-core.is-light .holo-title {
  border-bottom: 1px solid rgba(0, 0, 0, 0.08) !important;
}

.holo-title {
  font-family: var(--font-family-header);
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-color);
  text-align: center;
}

.holo-matrix {
  width: 100%;
  max-height: 400px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.holo-matrix::-webkit-scrollbar {
  width: 6px;
}

.holo-matrix::-webkit-scrollbar-track {
  background: transparent;
}

.holo-matrix::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

.holo-core.is-light .holo-matrix::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1) !important;
}
</style>

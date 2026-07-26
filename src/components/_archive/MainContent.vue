<template>
  <main class="main-content">
    <slot></slot>
  </main>
</template>

<script setup lang="ts">
// Simple wrapper for main content area
// Keeps layout clean and simple
</script>

<style scoped>
.main-content {
  margin-left: 60px;
  padding: clamp(16px, 2vw, 24px);
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--color-bg, #0a0a0a);
  color: var(--color-text, #e8e8e8);
}

@media (prefers-color-scheme: light) {
  .main-content {
    background: var(--color-bg, #f8f9fa);
    color: var(--color-text, #1a1a1a);
  }
}
</style>


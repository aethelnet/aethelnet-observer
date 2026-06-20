<template>
  <div class="subgraph-node" style="padding: 16px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; height: 100%;">
    <div style="font-size: 32px; margin-bottom: 8px;">🌌</div>
    <div style="font-size: 12px; font-weight: bold; color: var(--color-text-main); margin-bottom: 16px;">
      DIMENSIONAL PORTAL
    </div>
    <button @click="$emit('enter')" style="padding: 8px 16px; background: var(--color-text-main); color: var(--color-bg-primary); border: none; font-weight: 900; font-family: var(--font-family-mono); cursor: pointer;">
      [ DIVE IN ]
    </button>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  node: any;
}>()
const emit = defineEmits(['enter'])
</script>

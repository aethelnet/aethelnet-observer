<template>
  <div class="persona-card" style="padding: 12px; background: #00bcd4; color: #1A1A1A; border: 2px solid #1A1A1A; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100px;">
    <div style="font-weight: 900; font-size: 14px;">{{ name }}</div>
    <div style="font-size: 10px; font-weight: bold; margin-top: 4px;">[PERSONA NODE]</div>
    <button @mousedown.stop @click.stop="$emit('edit', node)" style="margin-top: 8px; background: transparent; border: 1px solid #1A1A1A; padding: 2px 8px; font-size: 10px; cursor: pointer;">Rename</button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  node: any
}>()

const name = computed(() => {
  return props.node.content?.split(':')[2] || 'Anonymous'
})
</script>

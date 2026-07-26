<template>
  <HoloFrame 
    title="PERSONA CORE" 
    color="#00bcd4" 
    :width="240"
    @collapse="$emit('toggle-expand')"
    @action-primary="$emit('edit', node)"
  >
    <template #icon>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width:14px; height:14px;">
        <circle cx="12" cy="12" r="9" stroke-dasharray="2 4" />
        <circle cx="12" cy="12" r="3" fill="currentColor" opacity="0.8"/>
        <path d="M12 3 L12 6 M12 18 L12 21 M3 12 L6 12 M18 12 L21 12" />
      </svg>
    </template>
    
    <div class="persona-content">
      <div class="persona-avatar"></div>
      <div class="persona-name">{{ name }}</div>
      <div class="persona-id">{{ String(node?.id || '').substring(0, 8) }}</div>
    </div>
    
    <template #footer>
      Identity Anchor
    </template>
  </HoloFrame>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import HoloFrame from '../HoloFrame.vue'

const props = defineProps<{
  node: any
}>()

defineEmits(['edit', 'toggle-expand'])

const name = computed(() => {
  return props.node.content?.split(':')[2] || 'Anonymous'
})
</script>

<style scoped>
.persona-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px 0;
}

.persona-avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: radial-gradient(circle at top right, #00bcd4, #005f6b);
  box-shadow: 0 0 15px rgba(0, 188, 212, 0.4);
  margin-bottom: 12px;
}

.persona-name {
  font-size: 16px;
  font-weight: 900;
  color: #fff;
  letter-spacing: 1px;
}

.persona-id {
  font-size: 10px;
  color: #888;
  margin-top: 4px;
}
</style>

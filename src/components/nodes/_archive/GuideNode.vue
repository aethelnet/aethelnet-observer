<template>
  <div class="guide-card" style="padding: 16px; background: var(--color-bg-panel); color: var(--color-text-main); border: 2px solid var(--color-accent); box-shadow: 4px 4px 0 rgba(0,0,0,0.5); display: flex; flex-direction: column; max-width: 300px;">
    <div style="font-weight: 900; font-size: 16px; color: var(--color-accent); border-bottom: 2px solid var(--border-color); padding-bottom: 8px; margin-bottom: 8px; text-transform: uppercase;">[ AETHEL_DOCS ]</div>
    <div style="font-size: 12px; line-height: 1.5; max-height: 200px; overflow-y: auto;">
      <MarkdownRenderer :content="markdownContent" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import MarkdownRenderer from '../MarkdownRenderer.vue'

const props = defineProps<{
  node: any
}>()

const markdownContent = computed(() => {
  return props.node.content?.replace(/^APP:Guide:/, '').trim() || ''
})
</script>

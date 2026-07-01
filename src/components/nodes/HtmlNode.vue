<template>
  <div class="html-node-container">
    <div class="editor-pane">
      <div class="pane-header">[ CODE ]</div>
      <textarea 
        v-model="rawHtml" 
        @blur="saveHtml" 
        class="code-textarea"
        spellcheck="false"
      ></textarea>
    </div>
    <div class="preview-pane">
      <div class="pane-header render-header">[ LIVE RENDER ]</div>
      <iframe :srcdoc="sanitizedHtml" sandbox="allow-scripts" class="render-frame"></iframe>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

const props = defineProps<{
  node: any
}>()

const emit = defineEmits(['update'])

const rawHtml = ref('')

// Initialize on mount and watch for changes
watch(() => props.node.content, (newContent) => {
  if (newContent) {
    rawHtml.value = newContent.replace(/^APP:Html\s*/i, '')
  }
}, { immediate: true })

const sanitizedHtml = computed(() => {
  let content = rawHtml.value || ''
  
  // Basic Markdown Parsing
  content = content
    .replace(/^### (.*$)/gim, '<h3 style="color:#00FF41;">$1</h3>')
    .replace(/^## (.*$)/gim, '<h2 style="color:#00FF41;">$1</h2>')
    .replace(/^# (.*$)/gim, '<h1 style="color:#00FF41;">$1</h1>')
    .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
    .replace(/\n/gim, '<br>')

  return `
    <html>
      <head>
        <style>
          /* Inject a tiny bit of modern reset for the iframe */
          body { font-family: 'Inter', -apple-system, sans-serif; margin: 0; padding: 12px; color: #111; background: #fff; box-sizing: border-box; }
          * { box-sizing: inherit; }
        </style>
      </head>
      <body>
        ${content}
      </body>
    </html>
  `
})

function saveHtml() {
  const newContent = 'APP:Html\n' + rawHtml.value
  props.node.content = newContent
  emit('update', props.node, undefined, newContent)
}
</script>

<style scoped>
.html-node-container {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 400px;
  background: transparent;
  border: none;
  font-family: var(--font-family-mono);
}

.pane-header {
  font-size: 10px;
  font-weight: 800;
  padding: 8px 16px;
  background: rgba(0, 0, 0, 0.2);
  color: var(--color-text-accent);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.render-header {
  background: rgba(224, 60, 49, 0.1);
  color: #E03C31;
}

.editor-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.code-textarea {
  flex: 1;
  width: 100%;
  background: rgba(0, 0, 0, 0.3);
  color: var(--color-text-main);
  border: none;
  padding: 12px;
  font-family: var(--font-family-mono, monospace);
  font-size: 12px;
  resize: none;
  outline: none;
  box-sizing: border-box;
}

.preview-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: transparent;
}

.render-frame {
  width: 100%;
  height: 100%;
  flex: 1;
  border: none;
  background: rgba(250, 250, 250, 0.95);
  border-bottom-left-radius: 20px;
  border-bottom-right-radius: 20px;
}
</style>

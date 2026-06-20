<template>
  <div class="html-node-container" @mousedown.stop @touchstart.stop>
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
  props.node.content = 'APP:Html\n' + rawHtml.value
}
</script>

<style scoped>
.html-node-container {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 400px;
  background: var(--color-bg-primary);
  border: 1px solid var(--border-color);
  font-family: var(--font-family-mono);
}

.pane-header {
  font-size: 10px;
  font-weight: 900;
  padding: 4px 8px;
  background: #1A1A1A;
  color: #888;
  border-bottom: 1px solid var(--border-color);
}

.render-header {
  background: #E03C31;
  color: #FFF;
}

.editor-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-bottom: 2px solid #E03C31;
}

.code-textarea {
  flex: 1;
  width: 100%;
  background: #050505;
  color: #00FF41;
  border: none;
  padding: 8px;
  font-family: 'Space Mono', monospace;
  font-size: 12px;
  resize: none;
  outline: none;
  box-sizing: border-box;
}

.preview-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #FFF;
}

.render-frame {
  flex: 1;
  width: 100%;
  border: none;
  background: #FFF;
}
</style>

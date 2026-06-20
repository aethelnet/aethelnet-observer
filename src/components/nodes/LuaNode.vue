<template>
  <div class="lua-node" @mousedown.stop @touchstart.stop>
    <div class="header">
      [ LUA ENGINE ]
    </div>
    
    <div class="editor-container">
      <textarea 
        v-model="script" 
        class="lua-editor"
        spellcheck="false" 
        placeholder="-- Write Lua script here...
-- Available: get_node_confidence('id')"
      ></textarea>
    </div>
    
    <div class="controls">
      <button class="run-btn" @click="executeLua" :disabled="isRunning">
        {{ isRunning ? 'EXECUTING...' : 'RUN SCRIPT' }}
      </button>
    </div>
    
    <div v-if="result !== null" class="result-box" :class="{ error: isError }">
      <div class="res-header">OUTPUT:</div>
      <div class="res-content">{{ result }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  node: any
}>()

const script = ref('-- Example:\nreturn get_node_confidence("' + props.node.id + '")')
const result = ref<string | null>(null)
const isError = ref(false)
const isRunning = ref(false)

async function executeLua() {
  if (!script.value) return
  isRunning.value = true
  isError.value = false
  result.value = null
  
  try {
    const API_BASE = (window as any).API_BASE || ''
    const url = API_BASE ? `${API_BASE}/lgnn/lua/execute` : `/api/lgnn/lua/execute`
    
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        script: script.value,
        node_id: props.node.id
      })
    })
    
    const data = await res.json()
    if (data.status === 'success') {
      result.value = data.result
    } else {
      isError.value = true
      result.value = data.message
    }
  } catch (err: any) {
    isError.value = true
    result.value = err.message
  } finally {
    isRunning.value = false
  }
}
</script>

<style scoped>
.lua-node {
  width: 320px;
  background: var(--color-bg-panel);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-node);
  font-family: var(--font-family-mono);
  display: flex;
  flex-direction: column;
}

.header {
  padding: 8px 12px;
  background: var(--color-bg-primary);
  border-bottom: 1px solid var(--border-color);
  font-weight: 900;
  font-size: 11px;
  color: #F2C12E; /* Lua yellowish */
  letter-spacing: 1px;
}

.editor-container {
  padding: 8px;
  background: #0A0A0A;
}

.lua-editor {
  width: 100%;
  height: 120px;
  background: transparent;
  color: #FFF;
  border: none;
  resize: vertical;
  font-family: 'Space Mono', monospace;
  font-size: 11px;
  outline: none;
  line-height: 1.4;
}

.controls {
  padding: 8px;
  border-top: 1px solid var(--border-color);
  background: var(--color-bg-panel);
  display: flex;
  justify-content: flex-end;
}

.run-btn {
  background: #F2C12E;
  color: #0A0A0A;
  border: none;
  font-weight: 900;
  cursor: pointer;
  padding: 4px 12px;
  font-family: 'Space Mono', monospace;
  font-size: 10px;
}

.run-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.result-box {
  padding: 8px;
  background: #000;
  border-top: 1px solid var(--border-color);
  font-size: 10px;
  color: #00FF41;
}

.result-box.error {
  color: #E03C31;
}

.res-header {
  font-weight: 900;
  margin-bottom: 4px;
  opacity: 0.7;
}

.res-content {
  white-space: pre-wrap;
  word-break: break-all;
}
</style>

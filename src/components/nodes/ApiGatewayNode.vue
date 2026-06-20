<template>
  <div class="api-node" @mousedown.stop @touchstart.stop>
    <div class="header">
      <span class="icon">⬡</span> API GATEWAY
    </div>
    
    <div class="description">
      Agent-friendly protocol for structured data. No scraping required.
    </div>
    
    <div class="config-row">
      <select v-model="method" class="api-select">
        <option>GET</option>
        <option>POST</option>
        <option>GraphQL</option>
      </select>
      <input 
        v-model="endpoint" 
        class="api-input" 
        placeholder="https://api.discogs.com/database/search?q=..." 
        spellcheck="false"
      />
    </div>
    
    <div class="config-row">
      <input 
        v-model="authHeader" 
        class="api-input" 
        placeholder="Header (e.g. Authorization: Bearer token) [Optional]" 
        spellcheck="false"
      />
    </div>

    <div v-if="method === 'POST' || method === 'GraphQL'" class="config-row">
      <textarea 
        v-model="bodyPayload" 
        class="api-textarea" 
        placeholder="JSON Body or GraphQL Query..."
        spellcheck="false"
      ></textarea>
    </div>
    
    <div class="controls">
      <button class="api-btn" @click="executeCall" :disabled="isLoading">
        {{ isLoading ? 'NEGOTIATING...' : 'EXECUTE CALL' }}
      </button>
    </div>
    
    <div v-if="result" class="result-box" :class="{ error: isError }">
      <div class="res-header">RESPONSE [{{ statusCode }}]</div>
      <div class="res-content">{{ result }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  node: any
}>()

const method = ref('GET')
const endpoint = ref('')
const authHeader = ref('')
const bodyPayload = ref('')

const isLoading = ref(false)
const isError = ref(false)
const result = ref<string | null>(null)
const statusCode = ref<number | string>('---')

async function executeCall() {
  if (!endpoint.value) return
  isLoading.value = true
  isError.value = false
  result.value = null
  statusCode.value = '...'
  
  try {
    const API_BASE = (window as any).API_BASE || ''
    const url = API_BASE ? `${API_BASE}/lgnn/api-gateway/proxy` : `/api/lgnn/api-gateway/proxy`
    
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        method: method.value,
        endpoint: endpoint.value,
        headers: authHeader.value,
        body: bodyPayload.value,
        node_id: props.node.id
      })
    })
    
    const data = await res.json()
    statusCode.value = data.status_code || 500
    
    if (data.status === 'success') {
      result.value = JSON.stringify(data.data, null, 2)
    } else {
      isError.value = true
      result.value = data.error || data.message || 'Unknown error'
    }
  } catch (err: any) {
    isError.value = true
    statusCode.value = 'ERR'
    result.value = err.message
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.api-node {
  width: 320px;
  background: var(--color-bg-panel);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-node);
  font-family: var(--font-family-mono);
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
}

.header {
  font-weight: 900;
  font-size: 12px;
  color: #B388FF;
  display: flex;
  align-items: center;
  gap: 6px;
  text-transform: uppercase;
}

.icon {
  animation: spin 10s linear infinite;
  display: inline-block;
}

@keyframes spin {
  100% { transform: rotate(360deg); }
}

.description {
  font-size: 9px;
  color: var(--color-text-muted);
  font-style: italic;
  margin-bottom: 4px;
}

.config-row {
  display: flex;
  gap: 4px;
}

.api-select {
  background: var(--color-bg-primary);
  border: 1px solid var(--border-color);
  color: #B388FF;
  font-family: var(--font-family-mono);
  font-size: 10px;
  font-weight: bold;
  outline: none;
  padding: 4px;
}

.api-input, .api-textarea {
  flex: 1;
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--color-text-main);
  font-family: var(--font-family-mono);
  font-size: 10px;
  padding: 4px 6px;
  outline: none;
}

.api-input:focus, .api-textarea:focus, .api-select:focus {
  border-color: #B388FF;
}

.api-textarea {
  height: 60px;
  resize: vertical;
}

.controls {
  display: flex;
  justify-content: flex-end;
  margin-top: 4px;
}

.api-btn {
  background: transparent;
  color: #B388FF;
  border: 1px solid #B388FF;
  font-weight: 900;
  cursor: pointer;
  padding: 4px 12px;
  font-family: 'Space Mono', monospace;
  font-size: 10px;
  transition: all 0.2s;
}

.api-btn:hover:not(:disabled) {
  background: #B388FF;
  color: var(--color-bg-primary);
}

.api-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  border-color: var(--border-color);
}

.result-box {
  margin-top: 8px;
  padding: 8px;
  background: #000;
  border-top: 1px solid var(--border-color);
  font-size: 9px;
  color: #B388FF;
  max-height: 150px;
  overflow-y: auto;
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

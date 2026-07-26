<template>
  <div class="api-node glass-panel">
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
  background: rgba(10, 10, 15, 0.85);
  backdrop-filter: blur(24px) saturate(200%);
  -webkit-backdrop-filter: blur(24px) saturate(200%);
  border: 1px solid rgba(179, 136, 255, 0.3);
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6), inset 0 0 20px rgba(179, 136, 255, 0.1);
  font-family: var(--font-family-mono);
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  color: #fff;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
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
  background: rgba(179, 136, 255, 0.1);
  color: #B388FF;
  border: 1px solid rgba(179, 136, 255, 0.4);
  font-weight: 900;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 6px;
  font-family: 'Space Mono', monospace;
  font-size: 10px;
  transition: all 0.3s;
}

.api-btn:hover:not(:disabled) {
  background: rgba(179, 136, 255, 0.2);
  box-shadow: 0 0 15px rgba(179, 136, 255, 0.4);
  transform: translateY(-1px);
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

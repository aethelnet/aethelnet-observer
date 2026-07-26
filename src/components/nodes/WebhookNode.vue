<template>
  <div class="webhook-node glass-panel">
    <div class="header">
      <span class="icon">🔗</span> WEBHOOK
    </div>
    <input v-model="localUrl" @blur="saveUrl" @keydown.enter="saveUrl" @mousedown.stop placeholder="https://..." class="hook-input" spellcheck="false" />
    <button @mousedown.stop @click.stop="fireRequest" class="hook-btn" :disabled="buttonText !== 'FIRE REQUEST'">{{ buttonText }}</button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

const props = defineProps<{
  node: any
  nodes: any[]
  links: any[]
}>()

const emit = defineEmits(['update-node'])

const buttonText = ref('FIRE REQUEST')

const meta = computed(() => {
  if (typeof props.node.meta_data === 'string') {
    try { return JSON.parse(props.node.meta_data || '{}') } catch (e) { return {} }
  }
  return props.node.meta_data || {}
})

const localUrl = ref(meta.value.url || '')

// Keep localUrl in sync if meta changes externally
watch(() => meta.value.url, (newUrl) => {
  if (newUrl !== localUrl.value) {
    localUrl.value = newUrl || ''
  }
})

function saveUrl() {
  if (localUrl.value === meta.value.url) return
  const newMeta = { ...meta.value, url: localUrl.value }
  emit('update-node', props.node, newMeta)
}

async function fireRequest() {
  const currentUrl = localUrl.value
  if (!currentUrl || !currentUrl.startsWith('http')) {
    alert("Please enter a valid webhook URL starting with http")
    return
  }
  
  const payloadData: string[] = []
  let injectedSecrets: Record<string, string> = {}

  for (const link of props.links) {
    const sourceId = link.source.id ?? link.source
    const targetId = link.target.id ?? link.target
    if (targetId === props.node.id) {
      const sourceNode = props.nodes.find(n => n.id === sourceId)
      if (sourceNode) {
        if (sourceNode.content) {
          payloadData.push(sourceNode.content)
        }
        // Extract vault secrets if source is a Vault node
        if (sourceNode.source_tag === 'vault' || sourceNode.label?.includes('Vault')) {
           const stored = localStorage.getItem(`aethel_vault_${sourceId}`)
           if (stored) {
             try {
               const secrets = JSON.parse(stored)
               injectedSecrets = { ...injectedSecrets, ...secrets }
             } catch(e) {}
           }
        }
      }
    }
  }
  
  try {
    buttonText.value = "FIRING..."
    
    const API_BASE = (window as any).API_BASE || ''
    const backendUrl = API_BASE ? `${API_BASE}/lgnn/webhook/fire` : '/api/lgnn/webhook/fire'
    
    const res = await fetch(backendUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url: currentUrl,
        payload: {
          source: "Aethelnet Graph Engine",
          timestamp: new Date().toISOString(),
          data: payloadData.join('\n\n')
        },
        secrets: injectedSecrets
      })
    })
    
    if (!res.ok) throw new Error("Backend execution failed")
    
    buttonText.value = "FIRED!"
    setTimeout(() => buttonText.value = "FIRE REQUEST", 2000)
  } catch (err) {
    console.error("Webhook failed:", err)
    alert("Failed to fire webhook via backend: " + err)
    buttonText.value = "ERROR!"
  }
}
</script>

<style scoped>
.webhook-node {
  width: 100%;
  height: 100%;
  background: var(--color-bg-primary);
  border: 2px solid #000000;
  box-shadow: 4px 4px 0px #000000;
  font-family: var(--font-family-mono);
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  color: #000000;
  min-height: 160px;
}

.header {
  font-weight: 900;
  font-size: 16px;
  color: #000000;
  display: flex;
  align-items: center;
  gap: 8px;
  text-transform: uppercase;
}

.hook-input {
  background: #ffffff;
  border: 2px solid #000000;
  border-radius: 0;
  color: #000000;
  font-family: var(--font-family-mono);
  font-size: 14px;
  padding: 12px;
  outline: none;
  margin-top: 8px;
}

.hook-input:focus {
  background: #f0f0f0;
  box-shadow: 4px 4px 0px #000000;
}

.hook-btn {
  margin-top: auto;
  background: #ffffff;
  color: #000000;
  border: 2px solid #000000;
  font-weight: 900;
  cursor: pointer;
  padding: 12px;
  border-radius: 0;
  font-family: var(--font-family-mono);
  font-size: 14px;
  text-transform: uppercase;
  box-shadow: 2px 2px 0px #000000;
}

.hook-btn:hover:not(:disabled) {
  background: #000000;
  color: #ffffff;
  transform: translate(-2px, -2px);
  box-shadow: 4px 4px 0px #000000;
}

.hook-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
}
</style>

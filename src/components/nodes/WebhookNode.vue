<template>
  <div class="webhook-card" style="padding: 12px; background: #FF9800; color: #1A1A1A; border: 2px solid #1A1A1A; display: flex; flex-direction: column; min-height: 120px;">
    <div style="font-weight: 900; font-size: 14px; text-transform: uppercase;">[ API HOOK ]</div>
    <input v-model="localUrl" @blur="saveUrl" @keydown.enter="saveUrl" @mousedown.stop placeholder="https://..." style="margin-top: 8px; padding: 4px; border: 2px solid #1A1A1A; font-family: 'Space Mono', monospace; font-size: 10px;" />
    <button @mousedown.stop @click.stop="fireRequest" style="margin-top: auto; background: #1A1A1A; color: #FF9800; border: none; padding: 4px 12px; font-weight: 900; cursor: pointer; font-size: 10px;">{{ buttonText }}</button>
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

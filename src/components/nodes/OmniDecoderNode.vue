<template>
  <div class="omni-decoder-node" @mousedown.stop @touchstart.stop>
    
    <div class="omni-header">
      <div class="header-title">[ OMNI DECODER ]</div>
      <div class="header-icon"><i class="fas fa-magic"></i>✨</div>
    </div>
    
    <div class="omni-body">
      
      <!-- Target Node -->
      <div class="input-group">
        <label>SOURCE NODE ID</label>
        <input v-model="sourceNodeId" placeholder="e.g. n1234 or [[Node Name]]" class="sci-input" />
      </div>

      <!-- Format Selector -->
      <div class="input-group">
        <label>OUTPUT FORMAT</label>
        <select v-model="selectedFormat" class="sci-select">
          <option value="TEXT">TEXT (Markdown / JSON)</option>
          <option value="IMAGE">IMAGE (Stable Diffusion)</option>
          <option value="UI">UI COMPONENT (Vue/HTML)</option>
          <option value="AUDIO">AUDIO (Speech Synthesis)</option>
        </select>
      </div>

      <!-- Optional Prompt -->
      <div class="input-group">
        <label>PROMPT INSTRUCTION (OPTIONAL)</label>
        <input v-model="customPrompt" placeholder="How should it be decoded?" class="sci-input" />
      </div>

    </div>

    <!-- Decode Button -->
    <div class="omni-footer">
      <button class="decode-btn" @click="decode" :disabled="loading">
        <span class="btn-glow"></span>
        <span class="btn-text">{{ loading ? 'DECODING...' : 'DECODE TOPOLOGY' }}</span>
      </button>
    </div>

    <!-- Results Container -->
    <div v-if="result" class="results-container">
      
      <!-- TEXT Result -->
      <div v-if="result.format === 'TEXT'" class="result-text">
        {{ result.content }}
      </div>
      
      <!-- IMAGE Result -->
      <div v-if="result.format === 'IMAGE'" class="result-image">
        <img :src="result.content" />
      </div>
      
      <!-- UI Result -->
      <div v-if="result.format === 'UI'" v-html="result.content" class="result-ui"></div>
      
      <!-- AUDIO Result -->
      <div v-if="result.format === 'AUDIO'" class="result-audio">
        [AUDIO STREAM ACTIVE]
        {{ result.content }}
      </div>

    </div>
    
    <div v-if="error" class="error-msg">
      ERROR: {{ error }}
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'

const props = defineProps<{
  node: any
}>()

const sourceNodeId = ref('')
const selectedFormat = ref('TEXT')
const customPrompt = ref('')
const loading = ref(false)
const error = ref('')
const result = ref<any>(null)

// Initialize state from meta_data if available
onMounted(() => {
  if (props.node.meta_data) {
    try {
      const meta = JSON.parse(props.node.meta_data)
      if (meta.omni_state) {
        sourceNodeId.value = meta.omni_state.source || ''
        selectedFormat.value = meta.omni_state.format || 'TEXT'
        customPrompt.value = meta.omni_state.prompt || ''
        if (meta.omni_result) {
          result.value = meta.omni_result
        }
      }
    } catch(e) {}
  }
})

// Auto-resolve [[Node Name]] to node ID (Simulated for now, would need actual node mapping)
function resolveNodeId(input: string) {
  const match = input.match(/\[\[(.*?)\]\]/)
  if (match) {
    // We would look up the node by title here, but for simplicity we'll let the user use the ID
    // or we assume the link works if the backend supports title lookup.
    // Right now backend expects exact ID. Let's just strip brackets if they typed it.
    return match[1] // If backend supports title lookup, otherwise this fails.
  }
  return input
}

async function decode() {
  if (!sourceNodeId.value) {
    error.value = "Source Node ID is required."
    return
  }
  
  loading.value = true
  error.value = ''
  result.value = null
  
  const targetId = resolveNodeId(sourceNodeId.value)
  
  try {
    const API_BASE = (window as any).API_BASE || ''
    const url = API_BASE ? `${API_BASE}/lgnn/decoder/omni` : '/api/lgnn/decoder/omni'
    
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source_node: targetId,
        format: selectedFormat.value,
        prompt: customPrompt.value
      })
    })
    
    const data = await res.json()
    if (data.status === 'success') {
      result.value = {
        format: data.format,
        content: data.content
      }
      saveState()
    } else {
      error.value = data.message || "Decoding failed."
    }
  } catch (err: any) {
    console.error('Decoding error:', err)
    error.value = err.message || "Network error."
  } finally {
    loading.value = false
  }
}

// Persist the decoder state to the graph so it remembers its output when reloaded
async function saveState() {
  try {
    const API_BASE = (window as any).API_BASE || ''
    const metaStr = JSON.stringify({
      omni_state: {
        source: sourceNodeId.value,
        format: selectedFormat.value,
        prompt: customPrompt.value
      },
      omni_result: result.value
    })
    
    await fetch(`${API_BASE || '/api'}/lgnn/node`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id: props.node.id,
        meta_data: metaStr,
        text_content: props.node.text_content || "",
        source_tag: props.node.source_tag || "omni_decoder",
        is_grounded: props.node.is_grounded || false,
        confidence: props.node.confidence || 1.0,
        connections: props.node.connections || []
      })
    })
  } catch (e) {
    console.error("Failed to save Omni state", e)
  }
}

</script>

<style scoped>
.omni-decoder-node {
  display: flex;
  flex-direction: column;
  width: 340px;
  background: rgba(10, 15, 25, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(0, 243, 255, 0.3);
  border-radius: 12px;
  font-family: 'Inter', 'Space Mono', monospace;
  color: #fff;
  box-shadow: 0 15px 35px rgba(0,0,0,0.6), inset 0 0 20px rgba(0, 243, 255, 0.05);
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.omni-decoder-node:hover {
  box-shadow: 0 20px 45px rgba(0,0,0,0.7), inset 0 0 30px rgba(0, 243, 255, 0.15);
  transform: translateY(-2px);
  border-color: rgba(0, 243, 255, 0.6);
}

.omni-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background: linear-gradient(90deg, rgba(0, 243, 255, 0.1) 0%, transparent 100%);
  border-bottom: 1px solid rgba(255,255,255,0.05);
}

.header-title {
  font-weight: 900;
  font-size: 12px;
  letter-spacing: 2px;
  color: rgba(255,255,255,0.9);
}

.header-icon {
  font-size: 14px;
  color: #00F3FF;
  text-shadow: 0 0 8px #00F3FF;
}

.omni-body {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.input-group label {
  font-size: 9px;
  font-weight: 800;
  color: rgba(255,255,255,0.5);
  letter-spacing: 1px;
}

.sci-input, .sci-select {
  background: rgba(0,0,0,0.4);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 4px;
  color: #00F3FF;
  font-size: 11px;
  padding: 8px 10px;
  font-family: 'Space Mono', monospace;
  outline: none;
  transition: all 0.2s ease;
}

.sci-select {
  cursor: pointer;
}

.sci-select option {
  background: #111;
  color: #FFF;
}

.sci-input:focus, .sci-select:focus {
  border-color: #00F3FF;
  box-shadow: 0 0 10px rgba(0, 243, 255, 0.2);
  background: rgba(0, 243, 255, 0.05);
}

.omni-footer {
  padding: 16px;
  background: rgba(0,0,0,0.3);
  border-top: 1px solid rgba(255,255,255,0.05);
}

.decode-btn {
  position: relative;
  width: 100%;
  background: transparent;
  color: #FFF;
  border: 1px solid rgba(0, 243, 255, 0.5);
  border-radius: 6px;
  padding: 12px;
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 2px;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.3s ease;
}

.btn-glow {
  position: absolute;
  top: 0; left: -100%;
  width: 50%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(0, 243, 255, 0.4), transparent);
  transition: all 0.5s ease;
}

.decode-btn:not(:disabled):hover {
  background: rgba(0, 243, 255, 0.1);
  box-shadow: 0 0 20px rgba(0, 243, 255, 0.3);
}

.decode-btn:not(:disabled):hover .btn-glow {
  left: 100%;
}

.decode-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  border-color: rgba(255,255,255,0.2);
}

.results-container {
  margin: 0 16px 16px 16px;
  border-top: 1px dashed rgba(255,255,255,0.2);
  padding-top: 16px;
  font-family: 'Space Mono', monospace;
  font-size: 11px;
  max-height: 250px;
  overflow-y: auto;
}

.results-container::-webkit-scrollbar {
  width: 4px;
}
.results-container::-webkit-scrollbar-thumb {
  background: rgba(0, 243, 255, 0.3);
  border-radius: 2px;
}

.result-text {
  white-space: pre-wrap;
  word-break: break-word;
  color: rgba(255,255,255,0.8);
  line-height: 1.4;
}

.result-image img {
  max-width: 100%;
  border-radius: 4px;
  border: 1px solid rgba(0, 243, 255, 0.3);
  box-shadow: 0 0 15px rgba(0, 243, 255, 0.2);
}

.result-ui {
  background: rgba(255,255,255,0.9);
  color: #000;
  padding: 12px;
  border-radius: 4px;
  border: 1px solid rgba(0, 243, 255, 0.5);
}

.result-audio {
  color: #00F3FF;
  font-style: italic;
  padding: 8px;
  background: rgba(0, 243, 255, 0.05);
  border-radius: 4px;
  text-align: center;
}

.error-msg {
  margin: 0 16px 16px 16px;
  color: #FF3366;
  font-size: 10px;
  font-weight: bold;
  padding: 8px;
  background: rgba(255, 51, 102, 0.1);
  border: 1px solid rgba(255, 51, 102, 0.3);
  border-radius: 4px;
}
</style>

<template>
  <div class="prisma-node glass-panel">
    <div class="header">
      <div class="icon-wrap">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="12 2 2 22 22 22"></polygon>
          <line x1="12" y1="2" x2="12" y2="22"></line>
          <line x1="12" y1="12" x2="22" y2="22"></line>
        </svg>
      </div>
      <div class="title">PRISMA</div>
      <div class="subtitle">Social Noise Refraction</div>
    </div>
    
    <div class="content">
      <div class="input-feed">
        <label>Input Data Stream (Social Noise)</label>
        <textarea 
          v-model="rawInput" 
          placeholder="Paste TikTok transcript, X thread, or IG caption here..."
          @mousedown.stop @touchstart.stop
        ></textarea>
      </div>

      <div class="settings-toggle" @click="showSettings = !showSettings">
        <span class="toggle-icon">{{ showSettings ? '▼' : '▶' }}</span> 
        <span class="toggle-text">ADVANCED CONFIG</span>
      </div>

      <div class="settings-panel" v-if="showSettings">
        <div class="input-feed">
          <label>API Provider</label>
          <select v-model="apiProvider" @mousedown.stop @touchstart.stop>
            <option value="openrouter">OpenRouter (Default)</option>
            <option value="ollama">Ollama (Local/Uncensored)</option>
            <option value="openai">OpenAI (Direct)</option>
          </select>
        </div>
        
        <div class="input-feed" v-if="apiProvider !== 'ollama'">
          <label>Custom API Key</label>
          <input type="password" v-model="apiKey" placeholder="Leave empty for Aethelnet Budget..." @mousedown.stop @touchstart.stop />
        </div>

        <div class="input-feed">
          <label>Custom Model</label>
          <input type="text" v-model="customModel" placeholder="e.g. anthropic/claude-3-haiku, llama3..." @mousedown.stop @touchstart.stop />
        </div>

        <div class="input-feed">
          <label>Refraction Prompt Override</label>
          <textarea 
            v-model="customPrompt" 
            placeholder="Default: Extract 3-5 hard concrete verified facts..."
            @mousedown.stop @touchstart.stop
          ></textarea>
        </div>
      </div>

      <div class="action-bar">
        <button class="refract-btn" @click="refract" :disabled="isProcessing">
          <span v-if="isProcessing">Refracting...</span>
          <span v-else>Extract Hard Facts</span>
        </button>
      </div>

      <div v-if="facts.length > 0" class="output-facts">
        <div class="fact-item" v-for="(fact, i) in facts" :key="i">
          <div class="fact-icon">✓</div>
          <div class="fact-text">{{ fact }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  node?: any
}>()

const emit = defineEmits(['update', 'spawn-link', 'unpin', 'edit', 'toggle-expand', 'execute', 'save-edit', 'delete', 'enter', 'refresh'])

const rawInput = ref('')
const isProcessing = ref(false)
const facts = ref<string[]>([])

// Advanced config
const showSettings = ref(false)
const apiProvider = ref('openrouter')
const apiKey = ref('')
const customModel = ref('')
const customPrompt = ref('')


async function refract() {
  if (!rawInput.value.trim()) return
  
  isProcessing.value = true
  facts.value = []
  
  try {
    const API_BASE = (window as any).API_BASE || ''
    const url = API_BASE ? `${API_BASE}/lgnn/prisma/refract` : '/api/lgnn/prisma/refract'
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        raw_input: rawInput.value,
        custom_prompt: customPrompt.value || undefined,
        api_provider: apiProvider.value,
        api_key: apiKey.value || undefined,
        custom_model: customModel.value || undefined
      })
    })
    const data = await res.json()
    if (data.status === 'success' && data.facts && Array.isArray(data.facts)) {
      facts.value = data.facts
      emit('refresh') // Tell LgnnView to fetch new nodes!
    } else {
      facts.value = [data.message || `Failed to extract facts. Raw response: ${JSON.stringify(data)}`]
    }
  } catch (err: any) {
    facts.value = [`Network Error: ${err.message}`]
  } finally {
    isProcessing.value = false
  }
}
</script>

<style scoped>
.prisma-node {
  background: var(--color-bg-primary);
  width: 100%;
  height: 100%;
  color: var(--color-text-main);
  font-family: var(--font-family);
  display: flex;
  flex-direction: column;
}

.header {
  background: #ffffff;
  padding: 14px 18px;
  display: flex;
  align-items: center;
  border-bottom: 2px solid #000000;
}

.icon-wrap {
  width: 24px;
  height: 24px;
  margin-right: 10px;
  color: #000000;
}

.title {
  font-weight: 700;
  letter-spacing: 1px;
  font-size: 18px;
  color: #000000;
  text-transform: uppercase;
}

.subtitle {
  margin-left: auto;
  font-size: 12px;
  color: #333333;
  text-transform: uppercase;
  font-weight: bold;
}

.content {
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: #ffffff;
  flex: 1;
}

.input-feed label {
  display: block;
  font-size: 12px;
  color: #000000;
  margin-bottom: 6px;
  text-transform: uppercase;
  font-weight: bold;
}

textarea {
  width: 100%;
  height: 120px;
  background: #ffffff;
  border: 2px solid #000000;
  border-radius: 0;
  color: #000000;
  padding: 12px;
  font-size: 14px;
  resize: none;
  font-family: inherit;
  transition: none;
}

input, select {
  width: 100%;
  background: #ffffff;
  border: 2px solid #000000;
  border-radius: 0;
  color: #000000;
  padding: 12px;
  font-size: 14px;
  font-family: inherit;
  transition: none;
  box-sizing: border-box;
}

textarea:focus, input:focus, select:focus {
  outline: none;
  background: #f0f0f0;
  box-shadow: 4px 4px 0px #000000;
}

.settings-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px;
  user-select: none;
  border: 2px solid transparent;
}

.settings-toggle:hover {
  background: #000000;
  color: #ffffff;
}
.settings-toggle:hover .toggle-icon, .settings-toggle:hover .toggle-text {
  color: #ffffff;
}

.toggle-icon {
  font-size: 14px;
  color: #000000;
  font-weight: bold;
}

.toggle-text {
  font-size: 12px;
  color: #000000;
  font-weight: bold;
  text-transform: uppercase;
}

.settings-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  border: 2px solid #000000;
  background: #f9f9f9;
}

.action-bar {
  display: flex;
  justify-content: flex-end;
}

.refract-btn {
  background: #ffffff;
  border: 2px solid #000000;
  color: #000000;
  padding: 12px 24px;
  border-radius: 0;
  font-family: var(--font-family-mono);
  font-weight: bold;
  font-size: 14px;
  cursor: pointer;
  box-shadow: 2px 2px 0px #000000;
  text-transform: uppercase;
}

.refract-btn:hover:not(:disabled) {
  background: #000000;
  color: #ffffff;
  transform: translate(-2px, -2px);
  box-shadow: 4px 4px 0px #000000;
}

.refract-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
}

.output-facts {
  display: flex;
  flex-direction: column;
  gap: 12px;
  border-top: 2px solid #000000;
  padding-top: 16px;
}

.fact-item {
  display: flex;
  align-items: flex-start;
  background: #ffffff;
  border: 2px solid #000000;
  padding: 16px;
  box-shadow: 2px 2px 0px #000000;
}

.fact-icon {
  color: #000000;
  font-weight: bold;
  margin-right: 12px;
  font-size: 16px;
}

.fact-text {
  font-size: 14px;
  line-height: 1.5;
  color: #000000;
  font-weight: 500;
}
</style>

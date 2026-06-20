<template>
  <div class="prisma-node" @mousedown.stop>
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
  node: any
}>()

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
    const res = await fetch(`${API_BASE}/lgnn/prisma/refract`, {
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
    if (data.status === 'success' && data.facts) {
      facts.value = data.facts
    } else {
      facts.value = [data.message || 'Failed to extract facts']
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
  background: rgba(15, 15, 20, 0.95);
  border: 1px solid rgba(138, 43, 226, 0.4);
  border-radius: 12px;
  width: 320px;
  color: #fff;
  font-family: 'Inter', sans-serif;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), 0 0 20px rgba(138, 43, 226, 0.15);
  overflow: hidden;
  backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
}

.header {
  background: linear-gradient(90deg, rgba(138,43,226,0.2) 0%, rgba(0,212,255,0.1) 100%);
  padding: 12px 16px;
  display: flex;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.icon-wrap {
  width: 28px;
  height: 28px;
  margin-right: 12px;
  color: #00d4ff;
  filter: drop-shadow(0 0 5px rgba(0, 212, 255, 0.5));
}

.title {
  font-weight: 800;
  letter-spacing: 2px;
  font-size: 14px;
  background: -webkit-linear-gradient(#fff, #aaa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  margin-left: auto;
  font-size: 10px;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.content {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.input-feed label {
  display: block;
  font-size: 11px;
  color: #aaa;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

textarea {
  width: 100%;
  height: 80px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  color: #eee;
  padding: 10px;
  font-size: 12px;
  resize: none;
  font-family: inherit;
  transition: border-color 0.2s;
}

input, select {
  width: 100%;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  color: #eee;
  padding: 8px 10px;
  font-size: 12px;
  font-family: inherit;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

textarea:focus, input:focus, select:focus {
  outline: none;
  border-color: rgba(138, 43, 226, 0.5);
}

.settings-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 0;
  user-select: none;
  transition: opacity 0.2s;
}

.settings-toggle:hover {
  opacity: 0.8;
}

.toggle-icon {
  font-size: 10px;
  color: #00d4ff;
}

.toggle-text {
  font-size: 10px;
  color: #888;
  letter-spacing: 1px;
  font-weight: 600;
}

.settings-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-left: 8px;
  border-left: 2px solid rgba(138, 43, 226, 0.3);
}


.action-bar {
  display: flex;
  justify-content: flex-end;
}

.refract-btn {
  background: linear-gradient(135deg, #8a2be2, #00d4ff);
  border: none;
  color: white;
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: 600;
  font-size: 12px;
  cursor: pointer;
  transition: transform 0.1s, box-shadow 0.2s;
  box-shadow: 0 0 10px rgba(138, 43, 226, 0.3);
}

.refract-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 0 15px rgba(0, 212, 255, 0.4);
}

.refract-btn:disabled {
  opacity: 0.7;
  cursor: wait;
}

.output-facts {
  display: flex;
  flex-direction: column;
  gap: 10px;
  border-top: 1px dashed rgba(255, 255, 255, 0.1);
  padding-top: 16px;
}

.fact-item {
  display: flex;
  align-items: flex-start;
  background: rgba(0, 212, 255, 0.05);
  border-left: 3px solid #00d4ff;
  padding: 10px;
  border-radius: 0 6px 6px 0;
  animation: slideIn 0.3s ease-out forwards;
}

.fact-icon {
  color: #00d4ff;
  font-weight: bold;
  margin-right: 10px;
  margin-top: 2px;
  font-size: 12px;
}

.fact-text {
  font-size: 12px;
  line-height: 1.4;
  color: #ddd;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateX(-10px); }
  to { opacity: 1; transform: translateX(0); }
}
</style>

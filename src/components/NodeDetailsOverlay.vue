<template>
  <div class="node-details-overlay" v-if="node">
    <div class="glitch-line"></div>
    <div class="header">
      <span class="node-id">{{ node.id }}</span>
      <button class="close-btn" @click="$emit('close')">X</button>
    </div>
    
    <div class="content">
      <div class="type-badge" :class="node.type">
        {{ node.type ? node.type.toUpperCase() : 'UNKNOWN' }} NODE
      </div>
      
      <div class="metadata">
        <div class="meta-row">
          <span class="label">CONFIDENCE:</span>
          <div class="bar-container">
            <div class="bar" :style="{ width: `${(node.confidence || 0.5) * 100}%`, background: getConfidenceColor(node.confidence) }"></div>
          </div>
          <span class="val">{{ ((node.confidence || 0.5) * 100).toFixed(1) }}%</span>
        </div>
        
        <div class="meta-row">
          <span class="label">PLATEAU:</span>
          <div class="bar-container">
            <div class="bar" :style="{ width: `${(node.plateau_factor || 0) * 100}%`, background: '#ff3366' }"></div>
          </div>
          <span class="val">{{ ((node.plateau_factor || 0) * 100).toFixed(1) }}%</span>
        </div>
      </div>
      
      <div class="text-content">
        <div class="label">PAYLOAD / TEXT:</div>
        <p class="text-body">{{ node.text_content || 'No textual payload detected in this tensor.' }}</p>
      </div>
      
      <div class="text-content">
        <div class="label">TACTICAL LLM SYNTHESIS:</div>
        <input 
          type="text" 
          v-model="llmPrompt" 
          placeholder="e.g. Generate a Momentum strategy..." 
          style="width: 100%; background: transparent; border: 1px solid #555; color: #fff; padding: 5px; font-family: inherit; margin-bottom: 10px;"
        />
        <button class="action-btn highlight" style="width: 100%; border-color: #00aaff; color: #00aaff;" @click="synthesizeStrategy" :disabled="isSynthesizing">
          {{ isSynthesizing ? 'SYNTHESIZING...' : 'SYNTHESIZE STRATEGY' }}
        </button>
      </div>

      <div class="footer-actions">
        <button class="action-btn" @click="$emit('quarantine', node.id)">QUARANTINE</button>
        <button class="action-btn highlight" @click="$emit('resonate', node.id)">FORCE RESONANCE</button>
      </div>
    </div>
  </div>
<script setup>
import { ref } from 'vue'

const props = defineProps({
  node: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'quarantine', 'resonate', 'synthesis-success'])

const llmPrompt = ref('')
const isSynthesizing = ref(false)

const getConfidenceColor = (val) => {
  if (val > 0.8) return '#00ffcc';
  if (val > 0.5) return '#ffaa00';
  return '#ff3366';
}

const synthesizeStrategy = async () => {
  if (!llmPrompt.value || !props.node) return;
  isSynthesizing.value = true;
  
  try {
    const baseUrl = import.meta.env.VITE_API_URL || 'http://130.61.202.29:8000';
    const res = await fetch(`${baseUrl}/api/llm/synthesize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: llmPrompt.value, node_id: props.node.id })
    });
    
    if (res.ok) {
      const data = await res.json();
      console.log("[LLM] Synthesis complete:", data.code);
      llmPrompt.value = '';
      emit('synthesis-success', data);
    } else {
      console.error("[LLM] Synthesis failed:", await res.text());
    }
  } catch (err) {
    console.error("[LLM] Request error:", err);
  } finally {
    isSynthesizing.value = false;
  }
}
</script>

<style scoped>
.node-details-overlay {
  position: absolute;
  bottom: 30px;
  left: 30px;
  width: 380px;
  background: rgba(5, 5, 10, 0.95);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(0, 255, 204, 0.2);
  color: #fff;
  font-family: 'JetBrains Mono', monospace;
  z-index: 9998;
  box-shadow: 0 15px 40px rgba(0,0,0,0.8), inset 0 0 20px rgba(0,255,204,0.05);
  overflow: hidden;
  animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.glitch-line {
  height: 2px;
  width: 100%;
  background: #00ffcc;
  box-shadow: 0 0 10px #00ffcc;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 15px;
  background: rgba(0, 255, 204, 0.1);
  border-bottom: 1px solid rgba(0, 255, 204, 0.2);
}

.node-id {
  font-weight: 700;
  color: #00ffcc;
  font-size: 0.9rem;
  letter-spacing: 1px;
}

.close-btn {
  background: transparent;
  border: none;
  color: #888;
  font-family: inherit;
  font-weight: bold;
  cursor: pointer;
}

.close-btn:hover {
  color: #ff3366;
}

.content {
  padding: 15px;
}

.type-badge {
  display: inline-block;
  padding: 3px 8px;
  font-size: 0.65rem;
  font-weight: bold;
  border-radius: 4px;
  margin-bottom: 15px;
  border: 1px solid;
}

.type-badge.agent { color: #00ffaa; border-color: #00ffaa; background: rgba(0,255,170,0.1); }
.type-badge.data { color: #00aaff; border-color: #00aaff; background: rgba(0,170,255,0.1); }
.type-badge.concept { color: #ff3366; border-color: #ff3366; background: rgba(255,51,102,0.1); }

.metadata {
  margin-bottom: 15px;
}

.meta-row {
  display: flex;
  align-items: center;
  font-size: 0.75rem;
  margin-bottom: 8px;
}

.meta-row .label {
  width: 90px;
  color: #888;
}

.bar-container {
  flex: 1;
  height: 6px;
  background: rgba(255,255,255,0.1);
  margin: 0 10px;
  border-radius: 3px;
  overflow: hidden;
}

.bar {
  height: 100%;
  transition: width 0.3s ease;
}

.val {
  width: 45px;
  text-align: right;
}

.text-content {
  margin-bottom: 20px;
  background: rgba(0,0,0,0.5);
  padding: 10px;
  border-left: 2px solid #555;
}

.text-content .label {
  font-size: 0.65rem;
  color: #666;
  margin-bottom: 5px;
}

.text-body {
  margin: 0;
  font-size: 0.8rem;
  line-height: 1.4;
  color: #ccc;
  word-wrap: break-word;
}

.footer-actions {
  display: flex;
  gap: 10px;
}

.action-btn {
  flex: 1;
  background: transparent;
  border: 1px solid #555;
  color: #aaa;
  padding: 8px;
  font-family: inherit;
  font-size: 0.7rem;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  background: rgba(255,255,255,0.1);
  color: #fff;
}

.action-btn.highlight {
  border-color: #00ffcc;
  color: #00ffcc;
}

.action-btn.highlight:hover {
  background: rgba(0, 255, 204, 0.2);
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>

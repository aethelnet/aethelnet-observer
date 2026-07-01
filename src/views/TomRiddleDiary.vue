<template>
  <div class="diary-container" :class="{ 'is-minimized': isMinimized }">
    <div class="diary-header" @click="isMinimized = !isMinimized">
      <div class="diary-title">
        <span class="pulse-dot"></span> THE DIARY
      </div>
      <div class="diary-controls">
        <button class="icon-btn">{{ isMinimized ? '[+]' : '[-]' }}</button>
      </div>
    </div>
    
    <div class="diary-body" v-show="!isMinimized">
      <textarea 
        v-model="journalText" 
        class="diary-textarea" 
        placeholder="Dear Diary... (Start typing. The system is listening.)"
        @input="handleInput"
      ></textarea>
      <div class="diary-status">
        <span v-if="isProcessing" style="color: #F2C12E;">Synthesizing...</span>
        <span v-else style="color: #666;">Idle</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, defineEmits } from 'vue'
import { API_BASE } from '../shared/api.js'

const emit = defineEmits(['node-spawned'])

const isMinimized = ref(false)
const journalText = ref('')
const isProcessing = ref(false)

let debounceTimer: any = null

function handleInput() {
  if (debounceTimer) clearTimeout(debounceTimer)
  
  // Wait 3 seconds after the user stops typing before processing
  debounceTimer = setTimeout(() => {
    processJournal()
  }, 3000)
}

async function processJournal() {
  if (!journalText.value.trim() || isProcessing.value) return
  
  // Only process the last segment to avoid re-processing the whole book
  const segments = journalText.value.split('\n\n')
  const latestThought = segments[segments.length - 1]
  
  if (latestThought.length < 10) return // too short
  
  isProcessing.value = true
  try {
    const url = API_BASE ? `${API_BASE}/lgnn/macro/execute` : '/api/lgnn/macro/execute';
    
    // We hack the macro execute endpoint by sending a fake OPERATOR node request
    // This tells the backend to extract concepts from the latest thought and spawn them
    await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        node_id: "OPERATOR_DIARY_" + Date.now(),
        inputs: { "DIARY": latestThought },
        text_content: "Extrahiere 1-2 fundamentale Kernkonzepte oder Entitäten aus diesem Tagebuch-Eintrag. Mach es extrem kurz und prägnant.",
        // The backend expects PRISM instructions to know how to format it.
        // We'll pass it implicitly by making the backend recognize OPERATOR_DIARY.
      })
    })
    emit('node-spawned')
  } catch (e) {
    console.error("Diary processing failed", e)
  } finally {
    isProcessing.value = false
  }
}
</script>

<style scoped>
.diary-container {
  position: absolute;
  bottom: 20px;
  right: 20px;
  width: 400px;
  background: #F4F4F0;
  border: 2px solid #1A1A1A;
  box-shadow: -8px 8px 0 rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
  z-index: 1000;
  transition: transform 0.3s ease;
}

.diary-container.is-minimized {
  width: auto;
  transform: translateY(0);
}

.diary-header {
  background: #1A1A1A;
  color: #F4F4F0;
  padding: 8px 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  font-family: 'Space Mono', monospace;
  font-size: 12px;
  font-weight: bold;
}

.diary-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background: #E03C31;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(224, 60, 49, 0.7); }
  70% { box-shadow: 0 0 0 6px rgba(224, 60, 49, 0); }
  100% { box-shadow: 0 0 0 0 rgba(224, 60, 49, 0); }
}

.icon-btn {
  background: transparent;
  color: #F4F4F0;
  border: none;
  cursor: pointer;
  font-family: 'Space Mono', monospace;
  font-size: 12px;
}

.diary-body {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.diary-textarea {
  width: 100%;
  height: 200px;
  background: transparent;
  border: 1px dashed #CCC;
  padding: 8px;
  font-family: 'Space Mono', monospace;
  font-size: 14px;
  color: #1A1A1A;
  resize: vertical;
}

.diary-textarea:focus {
  outline: none;
  border-color: #1A1A1A;
}

.diary-status {
  font-size: 10px;
  font-family: 'Space Mono', monospace;
  text-align: right;
  text-transform: uppercase;
}
</style>
